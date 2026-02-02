__all__ = ["toggle_database_logic"]
import logging


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
    logging.info("\n" + "="*80)
    logging.info("[REQUEST] POST /api/db/toggle")
    logging.info("="*80)

    try:
        if not request_data or 'enabled' not in request_data:
            logging.error("[ERROR] Missing 'enabled' field in request")
            return {
                'success': False,
                'error': "Missing required field: 'enabled' (boolean)"
            }, 400

        enabled = request_data.get('enabled')

        if not isinstance(enabled, bool):
            logging.error("[ERROR] 'enabled' field must be a boolean")
            return {
                'success': False,
                'error': "'enabled' field must be a boolean"
            }, 400

        # enabled=True means DB should be active (DB_DISABLED=False)
        # enabled=False means DB should be disabled (DB_DISABLED=True)
        db_disabled_ref['value'] = not enabled

        status = "enabled" if enabled else "disabled"
        logging.info(f"[DB] Database operations {status}")
        logging.info("="*80 + "\n")

        return {
            'success': True,
            'message': f'Database operations {status}',
            'db_enabled': enabled
        }, 200

    except Exception as e:
        logging.error(f"[ERROR] Exception occurred: {type(e).__name__}")
        logging.error(f"[ERROR] Error message: {str(e)}")
        logging.error("="*80 + "\n")
        return {
            'success': False,
            'error': str(e)
        }, 500
