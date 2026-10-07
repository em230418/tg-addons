from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    rent_via_period_ok = fields.Boolean("Can be rented via attributes")

    @api.onchange("rent_via_period_ok")
    def _onchange_rent_via_period_ok(self):
        if self.rent_via_period_ok:
            self.rent_ok = False

    @api.onchange("rent_ok")
    def _onchange_rent_ok(self):
        if self.rent_ok:
            self.rent_via_period_ok = False

    @api.constrains("rent_ok", "rent_via_period_ok")
    def _check_rent_oks(self):
        for record in self:
            if record.rent_ok and record.rent_via_period_ok:
                raise ValidationError(
                    _("Product cannot be rented with and without attributes")
                )

    @api.constrains("rent_ok", "rent_via_period_ok")
    def _check_rent_attributes(self):
        for record in self:
            if not record.rent_via_period_ok:
                period_attibutes = record.attribute_line_ids.mapped(
                    "attribute_id"
                ).filtered("is_period")
                if period_attibutes:
                    raise ValidationError(
                        _(
                            "Cannot use period attributes, "
                            "if product is not marked as can be rented via attributes"
                        )
                    )
