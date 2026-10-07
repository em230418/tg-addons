from odoo import models


class Product(models.Model):
    _inherit = "product.product"

    def _has_period_attributes(self):
        return self.product_tmpl_id._has_period_attributes()
