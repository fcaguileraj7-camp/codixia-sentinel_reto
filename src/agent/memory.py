"""
Módulo de Memoria Conversacional Multi-Turno y Persistencia Contextual
Hito S3: Reto Agente 2026 - SentinelGuard AI · Equipo Codixia

Rol 1: Fabián Aguilera (Lead Architect & Core Orchestrator)

Este módulo gestiona:
1. Almacenamiento y aislamiento de sesiones de chat (session_id).
2. Ventana deslizante (Sliding Window) para control estricto de tokens ($0.00 en local / optimizado en API).
3. Estado contextual de incidentes (amenaza en curso, seguimiento de preguntas).
4. Persistencia en memoria de viajes de transporte activos (placas, origen, destino, check-ins).
5. Exportación e importación de sesiones para integración con Streamlit o WhatsApp Webhook.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json


@dataclass
class ConversationTurn:
    """Representa un único turno de intercambio entre el usuario y SentinelGuard AI."""
    turn_id: int
    timestamp: str
    user_input: str
    agent_response: str
    mode: str
    risk_level: str
    action: str
    tool_results: Dict[str, Any] = field(default_factory=dict)
    police_report_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConversationSession:
    """Representa la sesión completa de un usuario con su historial y estado activo."""
    session_id: str
    created_at: str
    updated_at: str
    turns: List[ConversationTurn] = field(default_factory=list)
    active_trip: Optional[Dict[str, Any]] = None
    active_threat_context: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "turns": [turn.to_dict() for turn in self.turns],
            "active_trip": self.active_trip,
            "active_threat_context": self.active_threat_context,
        }


class ConversationMemory:
    """
    Gestor de memoria conversacional multi-turno con soporte para múltiples sesiones.
    Diseñado para operar con presupuesto blindado ($0.00 en pruebas locales) y eficiencia de tokens.
    """

    def __init__(self, max_turns_window: int = 5):
        """
        Args:
            max_turns_window: Número máximo de turnos recientes a incluir en la ventana
                              deslizante enviada al modelo para evitar saturar el prompt.
        """
        self.max_turns_window = max(1, max_turns_window)
        self.sessions: Dict[str, ConversationSession] = {}

    def get_or_create_session(self, session_id: str = "default") -> ConversationSession:
        """Obtiene una sesión existente o crea una nueva si no existe."""
        now = datetime.now(timezone.utc).isoformat()
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationSession(
                session_id=session_id,
                created_at=now,
                updated_at=now,
                turns=[],
                active_trip=None,
                active_threat_context=None,
            )
        return self.sessions[session_id]

    def add_turn(
        self,
        session_id: str,
        user_input: str,
        agent_decision: Dict[str, Any],
        tool_results: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        police_report: Optional[Dict[str, Any]] = None,
    ) -> ConversationTurn:
        """
        Registra un turno completo en el historial de la sesión y actualiza el estado contextual.
        """
        session = self.get_or_create_session(session_id)
        now = datetime.now(timezone.utc).isoformat()
        session.updated_at = now

        turn_id = len(session.turns) + 1
        police_report_id = None
        if police_report and isinstance(police_report, dict):
            police_report_id = police_report.get("report_id")

        mode = agent_decision.get("mode", "threat_inspection")
        risk_level = agent_decision.get("risk_level", "BAJO")
        action = agent_decision.get("action", "ANALYZE_ONLY")
        response_to_user = agent_decision.get("response_to_user", "")

        turn = ConversationTurn(
            turn_id=turn_id,
            timestamp=now,
            user_input=user_input,
            agent_response=response_to_user,
            mode=mode,
            risk_level=risk_level,
            action=action,
            tool_results=tool_results or {},
            police_report_id=police_report_id,
            metadata=metadata or {},
        )
        session.turns.append(turn)

        # Actualizar estado de viaje activo si una herramienta de ruta lo reportó
        if tool_results and "route" in tool_results:
            route_data = tool_results["route"]
            if isinstance(route_data, dict) and route_data.get("monitoring_active"):
                session.active_trip = route_data
            elif isinstance(route_data, dict) and route_data.get("status") in ["finished", "cancelled"]:
                session.active_trip = None

        # Actualizar contexto de amenaza si se detectó riesgo alto o crítico
        if risk_level in ["ALTO", "CRÍTICO"]:
            session.active_threat_context = {
                "last_incident_turn": turn_id,
                "risk_level": risk_level,
                "mode": mode,
                "summary": agent_decision.get("reasoning", "")[:200],
                "police_report_id": police_report_id,
            }

        return turn

    def get_history(self, session_id: str = "default", limit: Optional[int] = None) -> List[ConversationTurn]:
        """Retorna los turnos de la sesión, opcionalmente limitados a los últimos N turnos."""
        if session_id not in self.sessions:
            return []
        turns = self.sessions[session_id].turns
        if limit is not None and limit > 0:
            return turns[-limit:]
        return list(turns)

    def get_context_summary(self, session_id: str = "default", limit: Optional[int] = None) -> str:
        """
        Genera un bloque de texto compacto con los turnos previos para ser inyectado
        en el prompt de Grok o del agente, respetando la ventana deslizante.
        """
        n_turns = limit if limit is not None else self.max_turns_window
        recent_turns = self.get_history(session_id, limit=n_turns)
        session = self.get_or_create_session(session_id)

        if not recent_turns and not session.active_trip and not session.active_threat_context:
            return ""

        lines = []

        # Estado de viaje físico activo si existe
        if session.active_trip:
            trip = session.active_trip
            lines.append(
                f"[ESTADO ACTIVO: VIAJE EN CURSO | Placa: {trip.get('vehicle_plate', 'N/A')} | "
                f"Destino: {trip.get('destination', 'N/A')} | Monitoreo activo: Sí]"
            )

        # Contexto de amenaza reciente si existe
        if session.active_threat_context:
            threat = session.active_threat_context
            lines.append(
                f"[ALERTA PREVIA EN CURSO: Riesgo {threat.get('risk_level')} en Turno {threat.get('last_incident_turn')} | "
                f"Radicado CAI: {threat.get('police_report_id') or 'N/A'}]"
            )

        # Turnos previos formateados de forma compacta
        for turn in recent_turns:
            lines.append(
                f"Turno {turn.turn_id} | Usuario: \"{turn.user_input}\" -> "
                f"SentinelGuard [{turn.risk_level} / {turn.action}]: \"{turn.agent_response}\""
            )

        return "\n".join(lines)

    def get_active_trip(self, session_id: str = "default") -> Optional[Dict[str, Any]]:
        """Retorna los datos del viaje de taxi actualmente activo en la sesión."""
        session = self.get_or_create_session(session_id)
        return session.active_trip

    def set_active_trip(self, session_id: str, trip_data: Dict[str, Any]) -> None:
        """Registra o actualiza manualmente un viaje activo en la sesión."""
        session = self.get_or_create_session(session_id)
        session.active_trip = trip_data

    def clear_active_trip(self, session_id: str = "default") -> Optional[Dict[str, Any]]:
        """Finaliza y remueve el viaje activo de la sesión."""
        session = self.get_or_create_session(session_id)
        trip = session.active_trip
        session.active_trip = None
        return trip

    def clear_session(self, session_id: str = "default") -> None:
        """Limpia todo el historial y estado de una sesión específica."""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def clear_all(self) -> None:
        """Limpia todas las sesiones de memoria."""
        self.sessions.clear()

    def export_session(self, session_id: str = "default") -> Dict[str, Any]:
        """Exporta una sesión a diccionario serializable en JSON."""
        session = self.get_or_create_session(session_id)
        return session.to_dict()

    def import_session(self, session_data: Dict[str, Any]) -> ConversationSession:
        """Importa y reconstruye una sesión desde un diccionario exportado."""
        session_id = session_data.get("session_id", "default")
        session = self.get_or_create_session(session_id)
        session.created_at = session_data.get("created_at", session.created_at)
        session.updated_at = session_data.get("updated_at", session.updated_at)
        session.active_trip = session_data.get("active_trip")
        session.active_threat_context = session_data.get("active_threat_context")

        turns_data = session_data.get("turns", [])
        session.turns = [
            ConversationTurn(
                turn_id=t.get("turn_id", idx + 1),
                timestamp=t.get("timestamp", ""),
                user_input=t.get("user_input", ""),
                agent_response=t.get("agent_response", ""),
                mode=t.get("mode", "threat_inspection"),
                risk_level=t.get("risk_level", "BAJO"),
                action=t.get("action", "ANALYZE_ONLY"),
                tool_results=t.get("tool_results", {}),
                police_report_id=t.get("police_report_id"),
                metadata=t.get("metadata", {}),
            )
            for idx, t in enumerate(turns_data)
        ]
        return session
