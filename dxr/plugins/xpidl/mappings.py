from dxr.filters import LINE
from dxr.indexers import STRING_PROPERTY

# Like qualified line needle, but has no qualname
LINE_NEEDLE = {
    'type': 'object',
    'properties': {
        'name': STRING_PROPERTY,
        'start': {
            'type': 'integer',
            'index': 'false'  # just for highlighting
        },
        'end': {
            'type': 'integer',
            'index': 'false'
        }
    }
}

mappings = {
    LINE: {
        'properties': {
            'xpidl_var_decl': LINE_NEEDLE,
            'xpidl_function_decl': LINE_NEEDLE,
            'xpidl_derived': LINE_NEEDLE,
            'xpidl_type_decl': LINE_NEEDLE
        }
    }
}
