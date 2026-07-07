"""Knowledge Engine APIs — read-only. The registry is science; software may
query it, never mutate it. Mutation happens via files + review, per KB_ARCHITECTURE."""
from fastapi import APIRouter, Depends, HTTPException

from backend.app.knowledge_engine.registry import get_registry
from backend.app.knowledge_engine.validation_framework import score_corpus
from backend.app.knowledge_engine.moat_scorecard import compute_moat_scorecard
from backend.app.models.auth import User
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/stats")
def kb_stats(current_user: User = Depends(get_current_user)):
    return get_registry().stats()


@router.get("/validation/corpus")
def kb_validation_corpus(current_user: User = Depends(get_current_user)):
    """AFK-VAL-0001 corpus scorecard — descriptive only until N≥10 cases."""
    return score_corpus()


@router.get("/moat")
def kb_moat_scorecard(current_user: User = Depends(get_current_user)):
    """AFK-MOA-0001 machine-verified competitive moat vs generic AI business tools."""
    return compute_moat_scorecard()


@router.get("/search")
def kb_search(q: str = "", type: str | None = None, status: str | None = None,
              current_user: User = Depends(get_current_user)):
    results = get_registry().search(q, type, status)
    return [{"id": o["id"], "type": o["type"], "name": o["name"],
             "version": o["version"], "status": o["status"],
             "description": o.get("description", "")} for o in results[:100]]


@router.get("/objects/{object_id}")
def kb_get(object_id: str, current_user: User = Depends(get_current_user)):
    obj = get_registry().get(object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Knowledge object not found")
    return obj


@router.get("/objects/{object_id}/relationships")
def kb_relationships(object_id: str, current_user: User = Depends(get_current_user)):
    if not get_registry().get(object_id):
        raise HTTPException(status_code=404, detail="Knowledge object not found")
    return get_registry().relationships(object_id)
