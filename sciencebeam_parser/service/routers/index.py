import textwrap
from fastapi import APIRouter, Response


def create_index_router() -> APIRouter:
    router = APIRouter()

    @router.get('/')
    def index() -> Response:
        return Response(
            textwrap.dedent(
                '''
                <html>
                <head>
                    <title>ScienceBeam Parser</title>
                </head>
                <body>
                    <h1>ScienceBeam Parser</h1>
                    <p>
                    <a href="/api/docs">API docs</a>
                    </p>
                </body>
                </html>
                '''
            ).strip(),
            media_type='text/html'
        )

    return router
