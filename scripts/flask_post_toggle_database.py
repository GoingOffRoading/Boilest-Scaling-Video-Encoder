__all__ = ["toggle_database_logic"]


def toggle_database_logic(request_data, db_disabled_ref):
    """
    Toggle the database operations on/off
    Expects JSON body with: enabled (boolean)
    
    Args:
        request_data (dict): Request data containing enabled field
        db_disabled_ref (dict): Dictionary with 'value' key containing current DB_DISABLED state
        
    Returns:
        tuple: (response_data: dict, status_code: int)
    """
    print("\n" + "="*80)
    print("[REQUEST] POST /api/db/toggle")
    print("="*80)

    try:
        if not request_data or 'enabled' not in request_data:
            print("[ERROR] Missing 'enabled' field in request")
            return {
                'success': False,
                'error': "Missing required field: 'enabled' (boolean)"
            }, 400

        enabled = request_data.get('enabled')

        if not isinstance(enabled, bool):
            print("[ERROR] 'enabled' field must be a boolean")
            return {
                'success': False,
                'error': "'enabled' field must be a boolean"
            }, 400

        # enabled=True means DB should be active (DB_DISABLED=False)
        # enabled=False means DB should be disabled (DB_DISABLED=True)
        db_disabled_ref['value'] = not enabled

        status = "enabled" if enabled else "disabled"
        print(f"[DB] Database operations {status}")
        print("="*80 + "\n")

        return {
            'success': True,
            'message': f'Database operations {status}',
            'db_enabled': enabled
        }, 200

    except Exception as e:
        print(f"[ERROR] Exception occurred: {type(e).__name__}")
        print(f"[ERROR] Error message: {str(e)}")
        print("="*80 + "\n")
        return {
            'success': False,
            'error': str(e)
        }, 500
