'Namespace module'

from .admin import (
    AddUserView,
    ChangeCustomerEmailView,
    NewPasswordView,
    SendAdminEmailView,
    SendCustomerEmailView,
    SoftDeleteWinView,
)
from .flat_csv import CSVView, CompleteWinsCSVView, CurrentFinancialYearWins
from .model_views import (
    StandardPagination,
    WinViewSet,
    LimitedWinViewSet,
    ConfirmationViewSet,
    BreakdownViewSet,
    AdvisorViewSet,
    DetailsWinViewSet,
    WinDataHubView,
)
