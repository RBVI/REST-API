import falcon
from falcon_multipart.middleware import MultipartMiddleware
from multiprocessing import Manager
from .scnetviz import ScNetVizHandler
from .algorithms.algorithms import Algorithms
from .jobs import Jobs

manager = None

def create_app(mgr: Manager):
    manager = mgr
    api = falcon.API(middleware=[MultipartMiddleware()])

    # Provided for backwards compatibility
    api.add_route('/scnetviz/api/v1/umap', ScNetVizHandler())
    api.add_route('/scnetviz/api/v1/tsne', ScNetVizHandler())
    api.add_route('/scnetviz/api/v1/drawgraph', ScNetVizHandler())
    api.add_route('/scnetviz/api/v1/louvain', ScNetVizHandler())
    api.add_route('/scnetviz/api/v1/leiden', ScNetVizHandler())

    # New API
    jobs = Jobs(mgr)
    api.add_route('/status/{job_id}', jobs)
    api.add_route('/fetch/{job_id}', jobs)
    api.add_route('/terminate/{job_id}', jobs)
    algorithms = Algorithms(jobs)
    api.add_route('/services', algorithms)
    for algorithm in algorithms.get_algorithms():
        api.add_route('/service/'+algorithm, algorithms.get_algorithm(algorithm))

    return api


def get_app():
    return create_app(Manager())

