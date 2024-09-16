# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class Affiliate(models.Model):
    _name = "sale.affiliate"
    _order = "create_date desc"
    _description = "Sale Affiliate"

    name = fields.Char(required=True)
    partner_id = fields.Many2one(
        "res.partner",
        help="Partner associated with affiliation",
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        help="Company for affiliation",
    )
    sequence_id = fields.Many2one(
        "ir.sequence",
        required=True,
        default=lambda self: self._default_sequence_id(),
        help="Sequence to use for affiliate request naming",
    )
    request_ids = fields.One2many(
        "sale.affiliate.request",
        "affiliate_id",
        help="Requests generated by the affiliate",
    )
    valid_hours = fields.Integer(
        required=True,
        default=24,
        help="If the request is more than this many hours old, it will not be "
        "counted as a qualified conversion if a sale takes place. Use "
        "negative numbers to indicate infinity.",
    )
    valid_sales = fields.Integer(
        required=True,
        default=1,
        help="If the request is already associated with this many sales, it "
        "will not be counted as a qualified conversion in the event of a new "
        "sale. Use negative numbers to indicate infinity.",
    )
    conversion_rate = fields.Float(
        digits=(12, 4),
        compute="_compute_conversion_rate",
        help="Conversion count / Request count",
    )
    sales_per_request = fields.Float(
        digits=(12, 4),
        compute="_compute_sales_per_request",
        help="Sale count / Request count",
    )

    @api.depends("request_ids", "request_ids.sale_ids")
    def _compute_sales_per_request(self):
        for record in self:
            requests = record.request_ids
            sales_count = sum(len(request.sale_ids) for request in requests)
            try:
                record.sales_per_request = float(sales_count) / float(len(requests))
            except ZeroDivisionError:
                record.sales_per_request = 0

    @api.depends("request_ids", "request_ids.sale_ids")
    def _compute_conversion_rate(self):
        for record in self:
            requests = record.request_ids
            conversions = requests.filtered(lambda r: len(r.sale_ids) > 0)
            try:
                record.conversion_rate = float(len(conversions)) / float(len(requests))
            except ZeroDivisionError:
                record.conversion_rate = 0

    @api.model
    def _default_sequence_id(self):
        return self.env.ref(
            "website_sale_affiliate.request_sequence",
            raise_if_not_found=False,
        )

    def find_from_kwargs(self, **kwargs):
        """Find affiliate record based on kwargs"""
        try:
            affiliate_id = int(kwargs["aff_ref"])
            return self.search([("id", "=", affiliate_id)], limit=1)
        except KeyError:
            _logger.debug("Affiliate ID value not found")
        except ValueError:
            _logger.debug("Invalid affiliate ID value")
        return

    def get_request(self, **kwargs):
        self.ensure_one()
        Request = self.env["sale.affiliate.request"]
        try:
            name = kwargs["aff_key"]
            matching_request = Request.search(
                [
                    ("affiliate_id", "=", self.id),
                    ("name", "=", name),
                ],
                limit=1,
            )
        except KeyError:
            name = self.sequence_id.next_by_id()
            matching_request = None
        if not matching_request:
            matching_request = Request.create(
                {
                    "affiliate_id": self.id,
                    "name": name,
                }
            )
        return matching_request
