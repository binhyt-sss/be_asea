"""
CRUD operations package
Exports all CRUD functions for clean imports
"""

from crud.user_crud import (
    get_all_users,
    get_user_by_id,
    get_user_by_global_id,
    create_user,
    update_user,
    delete_user,
    get_users_by_zone,
    count_users,
    get_users_dict
)

from crud.zone_crud import (
    get_all_zones,
    get_zone_by_id,
    get_zone_with_users,
    create_zone,
    update_zone,
    delete_zone,
    count_zones,
    get_zones_with_user_counts
)

__all__ = [
    # User CRUD
    'get_all_users',
    'get_user_by_id',
    'get_user_by_global_id',
    'create_user',
    'update_user',
    'delete_user',
    'get_users_by_zone',
    'count_users',
    'get_users_dict',
    
    # Zone CRUD
    'get_all_zones',
    'get_zone_by_id',
    'get_zone_with_users',
    'create_zone',
    'update_zone',
    'delete_zone',
    'count_zones',
    'get_zones_with_user_counts',
]
