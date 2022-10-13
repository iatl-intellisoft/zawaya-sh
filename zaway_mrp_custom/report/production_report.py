# -*- coding: utf-8 -*-
from odoo import models, fields, api,tools, _
from odoo.tools import float_round
from odoo.exceptions import UserError, Warning
from datetime import datetime,date


class ProductionReport(models.AbstractModel):
    _name = 'report.zaway_mrp_custom.production_template'

    def _get_header_info(self, data):
        date_from = data['date_from']
        equipment_id = data['equipment_id']
        equipment_name = data['equipment_name']
        company_id = data['comp']


        return {
            'date_from': date_from,
            'equipment_id': equipment_id,
            'company_id': company_id,
            'equipment_name': equipment_name

        }

    def _get_production(self, data):

        production_list =[]

        from_dt = fields.Datetime.from_string(data['date_from'])
        to_dt = fields.Datetime.from_string(data['date_from'])


        from_date = datetime.strftime(from_dt, "%Y-%m-%d 00:00:00")
        to_date = datetime.strftime(to_dt, "%Y-%m-%d 23:59:59")

        mrp_production = self.env['mrp.production'].search([
            ('date_planned_start', '>=', from_date),
            ('date_planned_start', '<=',to_date),
            ('company_id','=',data['comp'])])


        if data['date_from'] and data['equipment_id']:
            print("11111111111111111111999",mrp_production)
            # for equipment in self.env['maintenance.equipment'].search([]):
            for mrp in mrp_production:
                for center in mrp.workorder_ids:
                    # if center.workcenter_id.equipment_ids:
                    for equi in center.workcenter_id.equipment_ids:
                        maintenance = []
                        components = [] 
                        production = []
                        print("??????????????????????????? equi.id",equi.id)
                        print("??????????????????????????? equipment_id",data['equipment_id'])
                        if equi.id == data['equipment_id']:
                            if mrp.request_ids:
                                for mainten in mrp.request_ids:
                                    if equi.id == mainten.equipment_id.id:
                                        maintenance.append({
                                            'name': mainten.name,
                                            'duration': mainten.duration,
                                            'description': mainten.description,
                                        })


                            if mrp.move_raw_ids:
                                for component in mrp.move_raw_ids:
                                    components.append({
                                        'product': component.product_id.name,
                                        'thickness': component.thickness,
                                        'tape_number': component.tape_number,
                                    })

                            if mrp.move_byproduct_ids:
                                for product in mrp.move_byproduct_ids:
                                    scrap_qty = 0
                                    for scrap in mrp.scrap_ids.filtered(lambda r : r.product_id.id == product.product_id.id and r.production_id.id == mrp.id):
                                        scrap_qty = scrap.scrap_qty
                                    production.append({
                                        'product': product.product_id.name,
                                        'tape_number': product.tape_number,
                                        'quantity_done': product.quantity_done,
                                        'scrap': scrap_qty
                                    })

                            production_list.append({
                                'name': equi.name,
                                'maintenance_list': maintenance,
                                'components': components,
                                'production': production,
                            })

            return production_list

        else:
            for equipment in self.env['maintenance.equipment'].search([]):
                print("11111111111111111111999",equipment.id)

                for mrp in mrp_production:
                    for center in mrp.workorder_ids:
                        for equi in center.workcenter_id.equipment_ids:
                            maintenance = []
                            components = [] 
                            production = []
                            if equi == equipment:
                                print(")))))))))))))))))))))))))))))))))")
                                if mrp.request_ids:
                                    for mainten in mrp.request_ids:
                                        maintenance.append({
                                            'name': mainten.name,
                                            'duration': mainten.duration,
                                            'description': mainten.description,
                                        })


                                if mrp.move_raw_ids:
                                    for component in mrp.move_raw_ids:
                                        components.append({
                                            'product': component.product_id.name,
                                            'thickness': component.thickness,
                                            'tape_number': component.tape_number,
                                        })

                                if mrp.move_byproduct_ids:
                                    for product in mrp.move_byproduct_ids:
                                        scrap_qty = 0
                                        for scrap in mrp.scrap_ids.filtered(lambda r : r.product_id.id == product.product_id.id and r.production_id.id == mrp.id):
                                            scrap_qty = scrap.scrap_qty
                                        production.append({
                                            'product': product.product_id.name,
                                            'tape_number': product.tape_number,
                                            'quantity_done': product.quantity_done,
                                            'scrap': scrap_qty
                                        })

                                production_list.append({
                                    'name': equi.name,
                                    'maintenance_list': maintenance,
                                    'components': components,
                                    'production': production,
                                })
  
        return production_list

    @api.model
    def _get_report_values(self, docids, data=None):
        data['records'] = self.env['mrp.production'].browse(data)
        docs = data['records']
        production_report = self.env['ir.actions.report']._get_report_from_name('zaway_mrp_custom.production_template')
        docargs = {

            'data': data,
            'docs': docs,
        }
        return {
            'doc_ids': self.ids,
            'doc_model': production_report.model,
            'docs': data,
            'get_info': self._get_header_info(data),
            'get_report': self._get_production(data),
        }