from odoo import fields, models, api

class Property(models.Model):
    _name = 'estate.property'
    _description = 'Property estate'

    name = fields.Char(string = "Name", required = True)
    type_id = fields.Many2one('estate.property.type', string= "Property Type")
    state = fields.Selection([
        ('new', 'New'),
        ('offer_received', 'Offer Received'),
        ('offer_accepted', 'Offer Accepted'),
        ('sold', 'Sold'),
        ('canceled', 'Canceled')
    ], default='new', string="Status")
    tag_ids = fields.Many2many('estate.property.tag', string="Property Tags")
    description = fields.Text(string = "Description")
    postcode = fields.Char(string = "Postcode")
    date_availability = fields.Date(string = "Available from", readonly = True)
    expected_price = fields.Float(string = "Expected Price")
    best_offer = fields.Float(string = "Best Offer")
    selling_price = fields.Float(string = "Selling Price")
    bedrooms = fields.Integer(string = "Bedrooms")
    living_area = fields.Integer(string = "Living Area(m2)")
    facades = fields.Integer(string = "Facades")
    garage = fields.Boolean(string = "Garage", default = False)
    garden = fields.Boolean(string = "Garden", default = False)
    garden_area = fields.Integer(string = "Garden Area")
    total_area = fields.Integer(string="Total Area", compute='_compute_total_area')
    garden_orientation = fields.Selection([
        ('north', 'North'), ('south', 'South'), ('east', 'East'), ('west', 'West')
    ], string = "Garden Orientation", default="north")
    offer_ids = fields.One2many('estate.property.offer', 'property_id', string = "Offers")
    sales_id = fields.Many2one('res.users', string="Salesman")
    buyer_id = fields.Many2one('res.partner', string="Buyer", domain=[('is_company', '=', True)])
    buyer_phone = fields.Char(string="Phone", related='buyer_id.phone')

    # these are attributes odoo create by default on every model:
    # id, create_date, create_uid, write_date, write_uid

    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        for rec in self:
            rec.total_area = rec.living_area + rec.garden_area

    def action_sold(self):
        self.state = 'sold'

    def action_cancel(self):
        self.state = 'canceled'

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for rec in self:
            rec.offer_count = len(rec.offer_ids)

    offer_count = fields.Integer(string="Offer Count", compute=_compute_offer_count)

class PropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Property type'

    name = fields.Char(string = "Name", required = True)

class PropertyTag(models.Model):
    _name = 'estate.property.tag'
    _description = 'Property Tag'

    name = fields.Char(string = "Name", required = True)
