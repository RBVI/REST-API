"""
Algorithm base class
"""

from uuid import UUID
import json

import falcon
from multiprocessing import Manager,Process

from .jobs import Jobs
import api.utils as utils

class BaseAlgorithm():
    jobs = None
    myjobs = {}

    def __init__(self, jobs: Jobs):
        self.jobs = jobs
        self.manager = jobs.get_manager()

    def on_post(self, req: falcon.Request, resp: falcon.Response):
        """ Get data and arguments """
        result = self.manager.dict()
        status = self.manager.dict()

        # Get our parameters
        args = self.get_args(req)

        # We need to do the load here because we can't pass a stream to our
        # child process
        args['json_data'] = json.load(req.get_param('data').file)

        uuid = self.jobs.create_job(req.path, self)
        t = Process(target=self.community_detection, args=(args, status, result))
        self.myjobs[uuid] = (status, result)
        t.start()
        resp.code = falcon.HTTP_200
        resp.body = json.dumps({'job_id': str(uuid)})

    def get_status(self, uid: UUID) -> str:
        if uid in self.myjobs:
            (status, result) = self.myjobs[uid]
            return status['status']
        return None

    def fetch_results(self, uid: UUID, req: falcon.Request, resp: falcon.Response):
        if uid in self.myjobs:
            (status, result) = self.myjobs[uid]
            # Add our response
            resp.body = utils.get_json_result(status, result)
            resp.code = falcon.HTTP_200
        else:
            resp.code = falcon.HTTP_400
            resp.body = str({'error':"no such job: "+str(uid)})

    def terminate(self, uid: UUID):
        # We can't really kill a thread, so we simply remove it from the queue
        self.jobs.remove_job(uid)
        del self.myjobs[uid]

