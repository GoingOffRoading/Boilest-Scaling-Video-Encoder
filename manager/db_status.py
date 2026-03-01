def get_database_status(db_disabled):
    """
    Get the current status of database operations
    
    Args:
        db_disabled (bool): The current state of the DB_DISABLED flag
        
    Returns:
        dict: Status information including enabled state and status message
    """
    enabled = not db_disabled
    status = "enabled" if enabled else "disabled"
    
    return {
        'success': True,
        'db_enabled': enabled,
        'status': status
    }
