import asyncio
import inspect
import time
import uuid
import sys 
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from datetime import datetime, timezone
from typing import Any, Annotated, TypedDict

from langgraph.graph import StateGraph, START, END

# ============================================================
# IMPORTS DES VRAIS AGENTS
# ============================================================

from agents.agent1_job_requirement.job_requirement import job_requirement_agent
from agents.agent2_cv_extraction.cv_extraction import extraire_profil_depuis_fichier
from agents.agent3_document_verification.agent3 import (
    verifier_documents,
    sans_donnees_sensibles,
)
from agents.agent4_matching.agent4 import faire_matching
from agents.agent5_report.agent5 import executer_agent5

from agents.common.schemas import (
    ExigencesStructurees,
    ProfilCandidat,
    VerificationDocuments,
    ResultatMatching,
    RapportCandidature,
)


# ============================================================
# 1. WORKFLOW CONFIGURATION
# ============================================================

MAX_RETRIES = 2
MAX_PARALLEL_AGENTS = 5

AGENT_NAMES = {
    "agent1": "Agent 1 - Job Requirements",
    "agent2": "Agent 2 - CV Extraction",
    "agent3": "Agent 3 - Document Verification",
    "agent4": "Agent 4 - Candidate Matching",
    "agent5": "Agent 5 - Report Generation",
}

RESULT_NAMES = {
    "agent1": "exigences",
    "agent2": "profil",
    "agent3": "verification",
    "agent4": "matching",
    "agent5": "rapport",
}


# ============================================================
# 2. UTILITY FUNCTIONS
# ============================================================

def get_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def serialize_result(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    return value


def merge_agent_states(existing: dict, updates: dict) -> dict:
    return {**existing, **updates}


# ============================================================
# 3. ADAPTATEURS
# ============================================================

def wrapper_agent1(texte_offre: str):
    return job_requirement_agent(texte_offre)


def wrapper_agent2(chemin: str):
    return extraire_profil_depuis_fichier(chemin)


def wrapper_agent3(profil, diplome_path: str, cin_path: str | None):
    """Agent 3 réel : image_cin=None si CIN absente."""
    resultat = verifier_documents(
        profil,
        image_diplome=diplome_path,
        image_cin=cin_path if cin_path else None,
    )
    return sans_donnees_sensibles(resultat)


def wrapper_agent4(exigences, profil, verification):
    return faire_matching(exigences, profil, verification)


def wrapper_agent5(exigences, profil, verification, matching):
    return executer_agent5({
        "agent1": exigences,
        "agent2": profil,
        "agent3": verification,
        "agent4": matching,
    })


# ============================================================
# 4. SHARED LANGGRAPH STATE
# ============================================================

class RecruitmentState(TypedDict, total=False):

    job_description: str
    cv_path: str
    diplome_path: str
    cin_path: str | None

    candidate_id: str
    job_id: str

    exigences: ExigencesStructurees | None
    profil: ProfilCandidat | None
    verification: VerificationDocuments | None
    matching: ResultatMatching | None
    rapport: RapportCandidature | None

    workflow_id: str
    status: str
    started_at: str
    finished_at: str

    agent_states: Annotated[dict[str, dict], merge_agent_states]
    logs: Annotated[list[dict], lambda old, new: old + new]
    errors: Annotated[list[dict], lambda old, new: old + new]


# ============================================================
# 5. GRAPH CONSTRUCTION
# ============================================================

def build_graph(
    max_retries: int = MAX_RETRIES,
    max_parallel_agents: int = MAX_PARALLEL_AGENTS,
):

    semaphore = asyncio.Semaphore(max_parallel_agents)

    async def execute_agent(agent_id: str, function, inputs: dict):

        agent_name = AGENT_NAMES[agent_id]

        logs = []
        errors = []

        started_at = get_timestamp()
        total_start = time.perf_counter()

        logs.append({
            "timestamp": started_at,
            "agent": agent_name,
            "event": "agent_started",
            "message": "Exécution de l'agent démarrée.",
            "attempt": None,
            "duration_seconds": None,
        })

        last_error = None

        async with semaphore:

            for attempt in range(1, max_retries + 2):

                attempt_start = time.perf_counter()

                logs.append({
                    "timestamp": get_timestamp(),
                    "agent": agent_name,
                    "event": "attempt_started",
                    "message": f"Tentative {attempt} sur {max_retries + 1}.",
                    "attempt": attempt,
                    "duration_seconds": None,
                })

                try:
                    if inspect.iscoroutinefunction(function):
                        output = await function(**inputs)
                    else:
                        output = await asyncio.to_thread(function, **inputs)

                    duration = round(time.perf_counter() - total_start, 4)

                    logs.append({
                        "timestamp": get_timestamp(),
                        "agent": agent_name,
                        "event": "agent_completed",
                        "message": "Agent exécuté avec succès.",
                        "attempt": attempt,
                        "duration_seconds": duration,
                    })

                    return {
                        "success": True,
                        "output": output,
                        "agent_state": {
                            "status": "termine",
                            "attempts": attempt,
                            "started_at": started_at,
                            "finished_at": get_timestamp(),
                            "duration_seconds": duration,
                            "error": None,
                        },
                        "logs": logs,
                        "errors": errors,
                    }

                except Exception as exc:

                    last_error = str(exc)

                    attempt_duration = round(
                        time.perf_counter() - attempt_start, 4
                    )

                    logs.append({
                        "timestamp": get_timestamp(),
                        "agent": agent_name,
                        "event": "attempt_failed",
                        "message": last_error,
                        "attempt": attempt,
                        "duration_seconds": attempt_duration,
                    })

                    if attempt <= max_retries:
                        logs.append({
                            "timestamp": get_timestamp(),
                            "agent": agent_name,
                            "event": "retry",
                            "message": "Nouvelle tentative de l'agent.",
                            "attempt": attempt,
                            "duration_seconds": None,
                        })
                        continue

        duration = round(time.perf_counter() - total_start, 4)

        error = {
            "agent_id": agent_id,
            "agent": agent_name,
            "message": last_error,
            "attempts": max_retries + 1,
        }

        errors.append(error)

        logs.append({
            "timestamp": get_timestamp(),
            "agent": agent_name,
            "event": "agent_failed",
            "message": "Nombre maximal de tentatives atteint.",
            "attempt": max_retries + 1,
            "duration_seconds": duration,
        })

        return {
            "success": False,
            "output": None,
            "agent_state": {
                "status": "erreur",
                "attempts": max_retries + 1,
                "started_at": started_at,
                "finished_at": get_timestamp(),
                "duration_seconds": duration,
                "error": last_error,
            },
            "logs": logs,
            "errors": errors,
        }

    def create_agent_node(agent_id, function, input_builder, result_key):
        async def agent_node(state: RecruitmentState):
            inputs = input_builder(state)
            execution = await execute_agent(
                agent_id=agent_id, function=function, inputs=inputs,
            )
            return {
                result_key: execution["output"],
                "agent_states": {agent_id: execution["agent_state"]},
                "logs": execution["logs"],
                "errors": execution["errors"],
            }
        return agent_node

    async def agent1_node(state: RecruitmentState):
        return await create_agent_node(
            "agent1",
            wrapper_agent1,
            lambda s: {"texte_offre": s["job_description"]},
            "exigences",
        )(state)

    async def agent2_node(state: RecruitmentState):
        return await create_agent_node(
            "agent2",
            wrapper_agent2,
            lambda s: {"chemin": s["cv_path"]},
            "profil",
        )(state)

    async def agent3_node(state: RecruitmentState):
        return await create_agent_node(
            "agent3",
            wrapper_agent3,
            lambda s: {
                "profil": s["profil"],
                "diplome_path": s["diplome_path"],
                "cin_path": s["cin_path"],
            },
            "verification",
        )(state)

    async def agent4_node(state: RecruitmentState):
        return await create_agent_node(
            "agent4",
            wrapper_agent4,
            lambda s: {
                "exigences": s["exigences"],
                "profil": s["profil"],
                "verification": s["verification"],
            },
            "matching",
        )(state)

    async def agent5_node(state: RecruitmentState):
        return await create_agent_node(
            "agent5",
            wrapper_agent5,
            lambda s: {
                "exigences": s["exigences"],
                "profil": s["profil"],
                "verification": s["verification"],
                "matching": s["matching"],
            },
            "rapport",
        )(state)

    def check_initial(state: RecruitmentState):
        return {}

    def check_agent3(state: RecruitmentState):
        return {}

    def check_agent4(state: RecruitmentState):
        return {}

    def route_after_initial(state: RecruitmentState):
        statuses = state["agent_states"]
        if (
            statuses["agent1"]["status"] == "termine"
            and statuses["agent2"]["status"] == "termine"
        ):
            return "agent3"
        return "finalize"

    def route_after_agent3(state: RecruitmentState):
        if state["agent_states"]["agent3"]["status"] == "termine":
            return "agent4"
        return "finalize"

    def route_after_agent4(state: RecruitmentState):
        if state["agent_states"]["agent4"]["status"] == "termine":
            return "agent5"
        return "finalize"

    async def finalize_node(state: RecruitmentState):

        agent_states = state["agent_states"]
        logs = []

        for agent_id, agent_state in list(agent_states.items()):
            if agent_state["status"] == "en_attente":
                agent_states = {
                    **agent_states,
                    agent_id: {
                        **agent_state,
                        "status": "bloque",
                        "finished_at": get_timestamp(),
                        "error": (
                            "Une ou plusieurs dépendances "
                            "n'ont pas terminé avec succès."
                        ),
                    },
                }
                logs.append({
                    "timestamp": get_timestamp(),
                    "agent": AGENT_NAMES[agent_id],
                    "event": "agent_blocked",
                    "message": "Une ou plusieurs dépendances ont échoué.",
                    "attempt": None,
                    "duration_seconds": None,
                })

        failed_agents = [
            agent_id
            for agent_id, agent_state in agent_states.items()
            if agent_state["status"] in {"erreur", "bloque"}
        ]

        if not failed_agents:
            workflow_status = "Analyse terminée"
            logs.append({
                "timestamp": get_timestamp(),
                "agent": "Orchestrateur",
                "event": "workflow_completed",
                "message": "Tous les agents ont terminé avec succès.",
                "attempt": None,
                "duration_seconds": None,
            })
        else:
            workflow_status = "Erreur de traitement"
            logs.append({
                "timestamp": get_timestamp(),
                "agent": "Orchestrateur",
                "event": "workflow_failed",
                "message": "Le workflow n'a pas pu terminer tous les agents.",
                "attempt": None,
                "duration_seconds": None,
            })

        return {
            "agent_states": agent_states,
            "status": workflow_status,
            "finished_at": get_timestamp(),
            "logs": logs,
        }

    workflow = StateGraph(RecruitmentState)

    workflow.add_node("agent1", agent1_node)
    workflow.add_node("agent2", agent2_node)
    workflow.add_node("agent3", agent3_node)
    workflow.add_node("agent4", agent4_node)
    workflow.add_node("agent5", agent5_node)

    workflow.add_node("check_initial", check_initial)
    workflow.add_node("check_agent3", check_agent3)
    workflow.add_node("check_agent4", check_agent4)
    workflow.add_node("finalize", finalize_node)

    workflow.add_edge(START, "agent1")
    workflow.add_edge(START, "agent2")

    workflow.add_edge(["agent1", "agent2"], "check_initial")

    workflow.add_conditional_edges(
        "check_initial",
        route_after_initial,
        {"agent3": "agent3", "finalize": "finalize"},
    )

    workflow.add_edge("agent3", "check_agent3")
    workflow.add_conditional_edges(
        "check_agent3",
        route_after_agent3,
        {"agent4": "agent4", "finalize": "finalize"},
    )

    workflow.add_edge("agent4", "check_agent4")
    workflow.add_conditional_edges(
        "check_agent4",
        route_after_agent4,
        {"agent5": "agent5", "finalize": "finalize"},
    )

    workflow.add_edge("agent5", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile()


# ============================================================
# 6. MAIN WORKFLOW FUNCTION
# ============================================================

async def run_workflow(
    job_description: str,
    cv_path: str,
    diplome_path: str,
    cin_path: str | None,
    candidate_id: str,
    job_id: str,
    max_retries: int = MAX_RETRIES,
    max_parallel_agents: int = MAX_PARALLEL_AGENTS,
) -> dict[str, Any]:

    required_inputs = {
        "job_description": job_description,
        "cv_path": cv_path,
        "diplome_path": diplome_path,
        "cin_path": cin_path,
        "candidate_id": candidate_id,
        "job_id": job_id,
    }

    for name, value in required_inputs.items():
        if name == "cin_path" and value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Missing or invalid input: {name}")

    if max_retries < 0:
        raise ValueError("max_retries cannot be negative.")
    if max_parallel_agents < 1:
        raise ValueError("max_parallel_agents must be at least 1.")

    workflow_id = str(uuid.uuid4())
    started_at = get_timestamp()

    agent_states = {
        agent_id: {
            "status": "en_attente",
            "attempts": 0,
            "started_at": None,
            "finished_at": None,
            "duration_seconds": None,
            "error": None,
        }
        for agent_id in AGENT_NAMES
    }

    initial_state: RecruitmentState = {
        "job_description": job_description,
        "cv_path": cv_path,
        "diplome_path": diplome_path,
        "cin_path": cin_path,
        "candidate_id": candidate_id,
        "job_id": job_id,

        "exigences": None,
        "profil": None,
        "verification": None,
        "matching": None,
        "rapport": None,

        "workflow_id": workflow_id,
        "status": "En cours de traitement",
        "started_at": started_at,
        "agent_states": agent_states,
        "logs": [{
            "timestamp": started_at,
            "agent": "Orchestrateur",
            "event": "workflow_started",
            "message": "Le workflow de recrutement a démarré.",
            "attempt": None,
            "duration_seconds": None,
        }],
        "errors": [],
    }

    graph = build_graph(
        max_retries=max_retries,
        max_parallel_agents=max_parallel_agents,
    )

    final_state = await graph.ainvoke(initial_state)

    serialized_results = {}
    for agent_id, result_name in RESULT_NAMES.items():
        output = final_state.get(result_name)
        if output is not None:
            serialized_results[result_name] = serialize_result(output)

    errors = final_state["errors"]

    return {
        "workflow_id": workflow_id,
        "candidate_id": candidate_id,
        "job_id": job_id,
        "status": final_state["status"],
        "started_at": started_at,
        "finished_at": final_state["finished_at"],
        "results": serialized_results,
        "agent_states": final_state["agent_states"],
        "logs": final_state["logs"],
        "errors": errors,
        "error": errors[0] if errors else None,
    }