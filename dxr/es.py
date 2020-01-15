"""Elasticsearch utilities not general enough to lift into pyelasticsearch"""

from flask import current_app
from elasticsearch import NotFoundError as ElasticHttpNotFoundError, RequestError
from werkzeug.exceptions import NotFound
from six import string_types
from six.moves.urllib.parse import urlparse
import certifi

from dxr.config import FORMAT


UNINDEXED_STRING = {
    'type': 'keyword',
    # doc_values and index must both be false to allow > 32k strings.
    'index': 'false',
    'doc_values': 'false'
}


UNANALYZED_STRING = {
    'type': 'keyword',
}


UNINDEXED_INT = {
    'type': 'integer',
    'index': 'false',
}


UNINDEXED_LONG = {
    'type': 'long',
    'index': 'false',
}


TREE = 'tree'  # 'tree' doctype


def frozen_configs():
    """Return a list of dicts, each describing a tree of the current format
    version."""
    return filtered_query(current_app.dxr_config.es_catalog_index,
                          TREE,
                          filter={'format': FORMAT},
                          sort=['name'],
                          size=10000)


def frozen_config(tree_name):
    """Return the bits of config that are "frozen" in place upon indexing.

    Return the ES "tree" doc for the given tree at the current format
    version. Raise NotFound if the tree

    """
    try:
        frozen = current_app.es.get(index=current_app.dxr_config.es_catalog_index,
                                    doc_type=TREE,
                                    id='%s/%s' % (FORMAT, tree_name))
        return frozen['_source']
    except (ElasticHttpNotFoundError, KeyError):
        # If nothing is found, we still get a hash, but it has no _source key.
        raise NotFound('No such tree as %s' % tree_name)


def es_alias_or_not_found(tree):
    """Return the elasticsearch alias for a tree, or raise NotFound."""
    return frozen_config(tree)['es_alias']


def filtered_query(*args, **kwargs):
    """Do a simple, filtered term query, returning an iterable of sources.

    This is just a mindless upfactoring. It probably shouldn't be blown up
    into a full-fledged API.

    ``include`` and ``exclude`` are mutually exclusive for now.

    """
    return sources(filtered_query_hits(*args, **kwargs))


def filtered_query_hits(index, doc_type, filter, sort=None, size=1, include=None, exclude=None):
    """Do a simple, filtered term query, returning an iterable of hit hashes."""
    query = {
        'query': {
            'bool' : {
                'filter': {
                    'term': filter
                }
            }
        }
    }
    if sort:
        query['sort'] = sort
    if include is not None:
        query['_source'] = {'includes': include}
    elif exclude is not None:
        query['_source'] = {'excludes': exclude}
    return current_app.es.search(
        body=query,
        index=index,
        doc_type=doc_type,
        size=size)['hits']['hits']


class IndexAlreadyExistsError(RequestError):
    """Exception raised on an attempt to create an index that already exists"""

def create_index_and_wait(es, index, settings=None):
    """Create a new index, and wait for all shards to become ready."""
    try:
        es.indices.create(index=index, body=settings)
    except RequestError as re:
        if re.error == "index_already_exists_exception":
            raise IndexAlreadyExistsError(re)
        raise
        
    es.cluster.health(index=index,
              wait_for_status='yellow',
              wait_for_no_relocating_shards=True,  # wait for all
              timeout='5m')


def sources(search_results):
    """Return just the _source attributes of some ES search results."""
    return [r['_source'] for r in search_results]

def host_urls_to_dicts(urls, username = None, password = None, port=9200,
                       ca_certs=certifi.where(), client_cert=None):
    """Convert pyelasticsearch-style transport URLs to elasticsearch host dicts."""
    if isinstance(urls, string_types):
        urls = [urls]
    urls = [u.rstrip('/') for u in urls]
    
    # Automatic node sniffing is off for now.
    parsed_urls = (urlparse(url) for url in urls)
    auth_default = None if username is None else (username, password)
    return [{'host': url.hostname,
              'port': url.port or port,
              'http_auth': (url.username, url.password) if
                           url.username or url.password else auth_default,
              'use_ssl': url.scheme == 'https',
              'verify_certs': True,
              'ca_certs': ca_certs,
              'cert_file': client_cert}
             for url in parsed_urls]

def index_op(doc, doc_type=None, index=None):
    op = dict()
    op["_source"] = doc
    if doc_type is not None:
        op["_type"] = doc_type
    if index is not None:
        op["_index"] = index
    return op
