# استيراد وظائف العرض المحددة من الملفات الفرعية
# product_transactions
from .product_transactions import (
    product_transaction_list, product_transaction_detail, product_transaction_post,
    product_transaction_unpost, product_transaction_add, product_transaction_edit,
    product_transaction_delete, product_movement_report, product_inventory
)

# expense_categories
from .expense_categories import (
    expense_category_list, expense_category_add, expense_category_edit, expense_category_delete
)

# income_categories
from .income_categories import (
    income_category_list, income_category_add, income_category_edit, income_category_delete
)

# expenses
from .expenses import (
    expense_list, expense_add, expense_edit, expense_delete, expense_post, expense_unpost,
    expense_detail
)

# incomes
from .incomes import (
    income_list, income_add, income_edit, income_delete, income_post, income_unpost,
    income_detail
)

# safe_deposits
from .safe_deposits import (
    safe_deposit_list, safe_deposit_add, safe_deposit_edit, safe_deposit_delete,
    safe_deposit_post, safe_deposit_unpost, safe_deposit_detail
)

# safe_withdrawals
from .safe_withdrawals import (
    safe_withdrawal_list, safe_withdrawal_add, safe_withdrawal_edit, safe_withdrawal_delete,
    safe_withdrawal_post, safe_withdrawal_unpost, safe_withdrawal_detail
)

# store_permits
from .store_permits import (
    store_permit_list, store_permit_add, store_permit_add_receive, store_permit_add_issue,
    store_permit_detail, store_permit_edit, store_permit_delete, store_permit_post,
    store_permit_unpost, store_permit_print
)

# reports
from .reports import (
    financial_transactions_report, financial_transactions_print,
    income_expense_report, income_expense_print,
    store_permits_report, store_permits_report_print
)
