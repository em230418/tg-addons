from odoo import _, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _enforce_rental_dates(self):
        for record in self:
            expected_start_date = None
            expected_end_date = None
            line_with_expected = self.env["sale.order.line"]

            for line in record.order_line.filtered(lambda x: not x.display_type):
                if not line.product_id.rent_via_period_ok:
                    continue

                period_ptav = line.product_no_variant_attribute_value_ids.filtered(
                    "is_period"
                )
                if not period_ptav:
                    raise UserError(
                        _(
                            "Period attribute is not set for product %s",
                            line.product_id.display_name,
                        )
                    )
                elif len(period_ptav) > 1:
                    raise UserError(
                        _(
                            "Too many period attributes for product %s",
                            line.product_id.display_name,
                        )
                    )

                start_date = period_ptav.start_date
                if not start_date:
                    raise UserError(
                        _("Period attribute %s does not have start date", period_ptav)
                    )

                end_date = period_ptav.end_date
                if not end_date:
                    raise UserError(
                        _("Period attribute %s does not have end date", period_ptav)
                    )

                if expected_start_date and expected_start_date != start_date:
                    raise UserError(
                        _(
                            "Conflict in start dates: %(expected_start_date)s from %(description_from_expected)s conflicts with %(given_start_date)s from %(description_from_given)s",  # noqa: E501
                            expected_start_date=expected_start_date,
                            description_from_expected=line_with_expected.display_name,
                            given_start_date=start_date,
                            description_from_given=line.display_name,
                        )
                    )

                if expected_end_date and expected_end_date != end_date:
                    raise UserError(
                        _(
                            "Conflict in end dates: %(expected_end_date)s from %(description_from_expected)s conflicts with %(given_end_date)s from %(description_from_given)s",  # noqa: E501
                            expected_end_date=expected_end_date,
                            description_from_expected=line_with_expected.display_name,
                            given_end_date=end_date,
                            description_from_givem=line.display_name,
                        )
                    )

                expected_start_date = start_date
                expected_end_date = end_date
                line_with_expected = line

            record.rental_start_date = expected_start_date
            record.rental_end_date = expected_end_date
