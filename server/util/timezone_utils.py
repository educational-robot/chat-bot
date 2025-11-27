from datetime import timezone, timedelta

# Timezone Việt Nam (GMT+7)
VIETNAM_TIMEZONE = timezone(timedelta(hours=7))

def get_vietnam_timezone():
    """Trả về timezone Việt Nam (GMT+7)"""
    return VIETNAM_TIMEZONE

def get_vietnam_now():
    """Trả về datetime hiện tại theo múi giờ Việt Nam"""
    from datetime import datetime
    return datetime.now(VIETNAM_TIMEZONE)

