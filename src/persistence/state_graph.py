"""State Graph and Idempotency Key Manager."""

import hashlib
import uuid
from typing import Optional, Tuple
from src.schemas.pipeline_state import PipelineState
from src.persistence.db import StateStore


def compute_idempotency_key(topic: str, retrieval_version: str = "v1", dictionary_hash: Optional[str] = None) -> str:
    """Computes deterministic hash from (primary_keyword, retrieval_version, dictionary_fingerprint).
    
    Any updates or tightening of posological limits in CLINICAL_DICTIONARY automatically
    invalidates stale checkpoints, preventing cache poisoning across medical guideline revisions.
    """
    from src.safety.clinical_dictionary import get_dictionary_fingerprint
    dict_hash = dictionary_hash or get_dictionary_fingerprint()
    norm = topic.strip().lower()
    raw = f"{norm}:{retrieval_version}:{dict_hash}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class StateGraphManager:
    """Manages append-only state transitions with checkpoint resumption."""

    def __init__(self, store: Optional[StateStore] = None):
        self.store = store or StateStore()

    def create_execution(self, raw_topic: str, retrieval_version: str = "v1") -> Tuple[str, str, PipelineState]:
        execution_id = str(uuid.uuid4())
        idempotency_key = compute_idempotency_key(raw_topic, retrieval_version)
        
        # Check if verified checkpoint already exists
        checkpoint = self.store.get_latest_checkpoint(idempotency_key)
        if checkpoint:
            return execution_id, idempotency_key, checkpoint

        initial_state = PipelineState(
            raw_topic=raw_topic,
            idempotency_key=idempotency_key
        )
        return execution_id, idempotency_key, initial_state

    def record_transition(
        self,
        execution_id: str,
        idempotency_key: str,
        step_name: str,
        state: PipelineState
    ) -> int:
        return self.store.save_snapshot(execution_id, idempotency_key, step_name, state)
