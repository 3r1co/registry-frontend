from sanic import Blueprint, response

status = Blueprint('status', url_prefix='/status')

@status.route("/")
async def get_jobs(request):
    if hasattr(request.app, "job_running"):
        return response.json(request.app.job_running)
    else:
        return response.json(False)
