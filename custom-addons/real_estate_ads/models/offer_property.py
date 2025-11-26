from odoo import _, fields, models, api
from datetime import timedelta
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class PropertyOffer(models.Model):
    _name = 'estate.property.offer'
    _description = 'Estate Property Offer'

    @api.depends('property_id', 'partner_id')
    def _compute_name(self):
        for rec in self:
            if rec.property_id and rec.partner_id:
                rec.name = f"Offer for {rec.property_id.name} by {rec.partner_id.name}"
            else:
                rec.name = False

    name = fields.Char(string="Description", compute=_compute_name)
    price = fields.Float(string = "Price")
    status = fields.Selection([
        ('accepted', 'Accepted'), ('refused', 'Refused'), ('pending', 'Pending')
    ], string="Status", default="pending")
    partner_id = fields.Many2one('res.partner', string="Customer")
    property_id = fields.Many2one('estate.property', string="Property")
    validity = fields.Integer(string="Validity")

    @api.model
    def _set_creation_date(self):
        return fields.Date.today()
    creation_date = fields.Date(string="Create Date", default=_set_creation_date)

    deadline = fields.Date(string="Deadline", compute='_compute_deadline', inverse='_inverse_deadline')

    # didnt work, but its another way to do it
    # _sql_constrains = [
    #     ('check_validity', 'check(validity > 0)', 'The validity must be positive')
    # ]

    @api.depends('validity', 'creation_date')
    # @api.depends_context('uid')
    def _compute_deadline(self):
        _logger.info("ENVIROMENT: %s", self.env.context)
        for rec in self:
            if rec.creation_date and rec.validity:
                rec.deadline = rec.creation_date + timedelta(days=rec.validity)
            else:
                rec.deadline = False

    def _inverse_deadline(self):
        for rec in self:
            if rec.deadline and rec.creation_date:
                rec.validity = (rec.deadline - rec.creation_date).days
            else:
                rec.validity = False

    # clean data for itself
    @api.autovacuum
    def _clean_offers(self):
        self.search([('status', '=', 'refused')]).unlink()

    @api.model_create_multi
    def create(self, vals):
        for rec in vals:
            if not rec.get('creation_date'):
                rec['creation_date'] = fields.Date.today()
        return super(PropertyOffer, self).create(vals)

    @api.constrains('validity')
    def _check_validity(self):
        for rec in self:
            if rec.creation_date and rec.validity:
                if rec.deadline <= rec.creation_date:
                    raise ValidationError(_("Deadline cannot be before creation date"))

    def write(self, vals):
        # _logger.info("WRITE on estate.property.offer with vals: %s", vals)
        partners = self.env['res.partner'].search([
            ('is_company','=', True)
        ], limit=10, order='name asc').mapped('name')
        _logger.info("partners: %s", partners)
        # print("Values -------->",vals)
        return super(PropertyOffer, self).write(vals)