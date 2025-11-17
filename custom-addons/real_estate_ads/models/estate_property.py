from odoo import fields, models

class Property(models.Model):
    _name = 'estate.property'
    _description = 'Property estate'

    name = fields.Char(string = "Name", required = True)
    type_id = fields.Many2one('estate.property.type', string= "Property Type")
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
    garden_orientation = fields.Selection([
        ('north', 'North'), ('south', 'South'), ('east', 'East'), ('west', 'West')
    ], string = "Garden Orientation", default="north")
    offer_ids = fields.One2many('estate.property.offer', 'property_id', string = "Offers")

    # these are attributes odoo create by default on every model:
    # id, create_date, create_uid, write_date, write_uid

class PropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Property type'

    name = fields.Char(string = "Name", required = True)

class PropertyT(models.Model):
    _name = 'estate.property.tag'
    _description = 'Property Tag'

    name = fields.Char(string = "Name", required = True)
