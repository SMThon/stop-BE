"""테이블 이름은 모두 app_ 접두사를 쓴다.

같은 Railway PostgreSQL을 기존 backend/(Node)와 함께 쓰더라도
그쪽의 api_users / purchases / subscriptions 테이블과 이름이 겹치지 않게 하기 위해서다.
"""

from app.models.event import Event
from app.models.notification_setting import NotificationSetting
from app.models.policy import Policy
from app.models.purchase import Purchase
from app.models.user import User

__all__ = ["Event", "NotificationSetting", "Policy", "Purchase", "User"]
