#! /usr/local/bin/python3
import falcon
import scanpy as sc
import pandas as pd
import os
import sys
import shutil
import logging
import warnings
import pathlib
import cgi
import zipfile
from urllib import parse


class ScNetVizHandler(object):
    min_genes=100
    min_cells=1
    normalize=True
    log1p=True
    hvg=True
    scale=True

    def on_post(self, req, resp):
        path = req.path
        source = req.get_param('source')
        accession = req.get_param('accession')
        #main()
        if (source is None or accession is None):
            resp.code = falcon.HTTP_400_BAD_REQUEST
            resp.body = {'error':"both source and accession must be specified"}
            return

        self.min_genes = get_param_as_int(req, 'min_genes', self.min_genes)
        self.min_cells = get_param_as_int(req, 'min_cells', self.min_cells)
        self.normalize = get_param_as_bool(req, 'normalize', True)
        self.log1p = get_param_as_bool(req, 'log1p', True)
        self.hvg = get_param_as_bool(req, 'hvg', True)
        self.scale = get_param_as_bool(req, 'scale', True)

        adata = None
        try:
            if path.endswith('/umap'):
                adata = self.handle_umap(req, resp, source, accession)
            elif path.endswith('/tsne'):
                adata = self.handle_tsne(req, resp, source, accession)
            elif path.endswith('/drawgraph'):
                adata = self.handle_tsne(req, resp, source, accession)
            elif path.endswith('/leiden'):
                adata = self.handle_tsne(req, resp, source, accession)
            elif path.endswith('/louvain'):
                adata = self.handle_tsne(req, resp, source, accession)
        except Exception as e:
            resp.status = falcon.HTTP_500
            resp.body = {'error': str(e)}
            return

        resp.status = falcon.HTTP_200

        # Note that we add the extra newline for compatability
        resp.body = adata.to_csv(header=None)+'\n'
        return



    def handle_umap(self, req, resp, source, accession):
        # umap arguments
        # scanpy.tl.umap(adata, min_dist=0.5, spread=1.0, n_components=2, maxiter=None, 
        #                alpha=1.0, gamma=1.0, negative_sample_rate=5, init_pos='spectral', 
        #                random_state=0, a=None, b=None, copy=False)
        #
        print('umap')
        n_neighbors = get_param_as_int(req, 'n_neighbors', 10)
        min_dist = get_param_as_float(req, 'min_dist', 0.5)

        print('getting file')
        adata = get_file(source, accession, req.get_param('file'))
        print('preprocessing')
        adata = preprocess(adata, n_neighbors=n_neighbors,
                           min_genes=self.min_genes,
                           min_cells=self.min_cells,
                           normalize=self.normalize,
                           log1p=self.log1p,
                           hvg=self.hvg,
                           scale=self.scale)
        print('calculating')
        sc.tl.umap(adata, min_dist=min_dist)
        print('returning')
        return pd.DataFrame(adata.obsm['X_umap'], index=adata.obs_names)

    def handle_tsne(self, req, resp, source, accession):
        # tSNE arguments
        #  scanpy.tl.tsne(adata, n_pcs=None, use_rep=None, perplexity=30, early_exaggeration=12, 
        #                 learning_rate=1000, random_state=0, use_fast_tsne=True, n_jobs=None, copy=False)
        #
        adata = get_file(source, accession, req.get_param('file'))
        adata = preprocess(adata,
                           min_genes=self.min_genes,
                           min_cells=self.min_cells,
                           normalize=self.normalize,
                           log1p=self.log1p,
                           hvg=self.hvg,
                           scale=self.scale)
        n_pcs = get_param_as_int(req, 'n_pcs', None)
        perplexity = get_param_as_float(req, 'perplexity', 30.0)
        learning_rate = get_param_as_float(req, 'learning_rate', 1000.0)
        early_exaggeration = get_param_as_float(req, 'early_exaggeration', 12.0)

        sc.tl.tsne(adata, n_pcs=n_pcs, perplexity=perplexity, learning_rate=learning_rate, 
                   early_exaggeration=early_exaggeration)
        return pd.DataFrame(adata.obsm['X_tsne'], index=adata.obs_names)

    def handle_drawgraph(self, req, resp, source, accession):
        # draw_graph arguments
        #  scanpy.tl.draw_graph(adata, layout='fa', init_pos=None, root=None, random_state=0, 
        #                       n_jobs=None, adjacency=None, key_added_ext=None, copy=False, **kwds)
        n_neighbors = get_param_as_int(req, 'n_neighbors', 10)
        layout = get_param_as_string(req, 'layout', 'fr')

        adata = get_file(source, accession, req.get_param('file'))
        adata = preprocess(adata, n_neighbors=n_neighbors,
                           min_genes=self.min_genes,
                           min_cells=self.min_cells,
                           normalize=self.normalize,
                           log1p=self.log1p,
                           hvg=self.hvg,
                           scale=self.scale)
        sc.tl.draw_graph(adata, layout=layout)
        return pd.DataFrame(adata.obsm['X_draw_graph_'+layout], index=adata.obs_names)

    def handle_louvain(self, req, resp, source, accession):
        # louvain arguments
        #  scanpy.tl.louvain(adata, resolution=None, random_state=0, restrict_to=None, 
        #                    key_added='louvain', adjacency=None, flavor='vtraag', directed=True, 
        #                    use_weights=False, partition_type=None, partition_kwargs=None, copy=False)
        #
        n_neighbors = get_param_as_int(req, 'n_neighbors', 15)
        adata = get_file(source, accession, req.get_param('file'))
        adata = preprocess(adata, n_neighbors=n_neighbors,
                           min_genes=self.min_genes,
                           min_cells=self.min_cells,
                           normalize=self.normalize,
                           log1p=self.log1p,
                           hvg=self.hvg,
                           scale=self.scale)
        sc.tl.louvain(adata)
        return adata.obs['louvain']

    def handle_leiden(self, req, resp, source, accession):
        n_neighbors = get_param_as_int(req, 'n_neighbors', 15)
        adata = get_file(source, accession, req.get_param('file'))
        adata = preprocess(adata, n_neighbors=n_neighbors,
                           min_genes=self.min_genes,
                           min_cells=self.min_cells,
                           normalize=self.normalize,
                           log1p=self.log1p,
                           hvg=self.hvg,
                           scale=self.scale)
        sc.tl.leiden(adata)
        return adata.obs['leiden']


def get_param_as_string(req, param, default):
    if req.has_param(param):
        return str(req.get_param(param))
    else:
        return default

def get_param_as_float(req, param, default):
    if req.has_param(param):
        return req.get_param_as_float(param)
    else:
        return default

def get_param_as_int(req, param, default):
    if req.has_param(param):
        return req.get_param_as_int(param)
    else:
        return default

def get_param_as_bool(req, param, default):
    if req.has_param(param):
        return req.get_param_as_bool(param)
    else:
        return default

def get_file(source, accession, matrixFile):
    matrix = zipfile.ZipFile(matrixFile.file, 'r')
    #matrix = zipfile.ZipFile(matrixFile, 'r')

    matrix.extractall("/tmp")
    filePath = "/tmp/"+source+"/"+accession
    adata = sc.read_10x_mtx(filePath, var_names="gene_symbols", cache=True)
    #shutil.rmtree(filePath)

    return adata

def preprocess(adata, n_neighbors=None, min_genes=100, min_cells=1, 
               normalize=True, log1p=True, 
               hvg=True, scale=True):

    # Filter options:
    # scanpy.pp.filter_cells(data, min_counts=None, min_genes=None, max_counts=None, 
    #                        max_genes=None, inplace=True, copy=False)
    # scanpy.pp.filter_genes(data, min_counts=None, min_cells=None, max_counts=None, 
    #                        max_cells=None, inplace=True, copy=False)
    #
    sc.pp.filter_cells(adata, min_genes=min_genes)
    sc.pp.filter_genes(adata, min_cells=min_cells)

    # normalization options
    #  scanpy.pp.normalize_total(adata, target_sum=None, exclude_highly_expressed=False, 
    #                            max_fraction=0.05, key_added=None, layers=None, layer_norm=None, 
    #                            inplace=True)
    if normalize is True:
      sc.pp.normalize_total(adata)

    if log1p is True:
        sc.pp.log1p(adata)

    #
    # scanpy.pp.highly_variable_genes(adata, min_disp=None, max_disp=None, min_mean=None, 
    #                                 max_mean=None, n_top_genes=None, n_bins=20, flavor='seurat', 
    #                                 subset=False, inplace=True, batch_key=None)
    if hvg is True:
        sc.pp.highly_variable_genes(adata)
        adata = adata[:, adata.var['highly_variable']]

    # Scal options
    # scanpy.pp.scale(data, zero_center=True, max_value=None, copy=False)
    if scale is True:
        sc.pp.scale(adata, max_value=10)

    if (n_neighbors != None):
        # neighbors options:
        #  scanpy.pp.neighbors(adata, n_neighbors=15, n_pcs=None, use_rep=None, knn=True, 
        #                      random_state=0, method='umap', metric='euclidean', metric_kwds={}, copy=False)
        try:
            sc.pp.neighbors(adata, n_neighbors=n_neighbors, n_pcs=40)
        except Exception as e:
            logging.debug('preprocess: got exception calculating neighbors: '+str(e))
    else:
        # PCA Options
        #  scanpy.tl.pca(data, n_comps=50, zero_center=True, svd_solver='auto', random_state=0, 
        #                return_info=False, use_highly_variable=None, dtype='float32', copy=False, 
        #                chunked=False, chunk_size=None)
        sc.tl.pca(adata, svd_solver='arpack')

    return adata
