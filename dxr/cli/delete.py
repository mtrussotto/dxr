from click import ClickException, command, echo, option
from elasticsearch import Elasticsearch, NotFoundError as ElasticHttpNotFoundError

from dxr.cli.utils import config_option, tree_names_argument
from dxr.config import FORMAT
from dxr.es import TREE, host_urls_to_dicts


@command()
@config_option
@option('--force', '-f',
        is_flag=True,
        help='Skip prompting for confirmation.')
@option('--all', '-a',
        is_flag=True,
        help='Delete all trees, and also delete the catalog index, in case it '
             'was somehow corrupted.')
@tree_names_argument
def delete(config, tree_names, all, force):
    """Delete indices and their catalog entries.

    This deletes the indices that have the format version of the copy of DXR
    this runs under.

    """
    es = Elasticsearch(host_urls_to_dicts(config.es_hosts))
    if all:
        echo('Deleting catalog...')
        es.indices.delete(index=config.es_catalog_index)
        # TODO: Delete tree indices as well.
    else:
        for tree_name in tree_names:
            frozen_id = '%s/%s' % (FORMAT, tree_name)
            try:
                frozen = es.get(index=config.es_catalog_index, doc_type=TREE, id=frozen_id)
            except ElasticHttpNotFoundError:
                raise ClickException('No tree "%s" in catalog.' % tree_name)
            # Delete the index first. That way, if that fails, we can still
            # try again; we won't have lost the catalog entry. Refresh is
            # infrequent enough that we wouldn't avoid a race around a
            # catalogued but deleted instance the other way around.
            try:
                es.indices.delete(index=frozen['_source']['es_alias'])
            except ElasticHttpNotFoundError:
                # It's already gone. Fine. Just remove the catalog entry.
                pass
            es.delete(index=config.es_catalog_index, doc_type=TREE, id=frozen_id)
