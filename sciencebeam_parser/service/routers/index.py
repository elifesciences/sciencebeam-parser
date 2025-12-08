from fastapi import APIRouter, Response


def create_index_router() -> APIRouter:
    router = APIRouter()

    @router.get('/')
    def index() -> Response:
        return Response('ScienceBeam Parser', media_type='text/plain')

    return router
