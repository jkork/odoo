from odoo import models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Handler method for creating a new quotation or sale order
    def _handle_create_new(self, sale_order):
        if sale_order.partner_id:
            order_url = sale_order._get_html_link(title=sale_order.name)
            message = f'A new Quotation or Sale Order {order_url} has been created.'
            sale_order.partner_id.message_post(
                body=message, 
                subtype_xmlid='mail.mt_comment', 
                body_is_html=True
            )

    # Handler method for quotation/sale order status change
    def _handle_order_status_change(self, sale_order, original_state):
        if sale_order.state != original_state and sale_order.partner_id:
            order_url = sale_order._get_html_link(title=sale_order.name)
            message = f'Quotation or Sale order {order_url} status changed to {sale_order.state}.'
            sale_order.partner_id.message_post(
                body=message, 
                subtype_xmlid='mail.mt_comment', 
                body_is_html=True
            )

    # Handler method for checking changes in order lines' quantity and unit price
    def _handle_order_lines_change(self, sale_order, original_lines):
        products = []
        for line in sale_order.order_line:
            if line.id in original_lines:
                original_qty = original_lines[line.id]['qty']
                original_price = original_lines[line.id]['price']
                
                new_qty = line.product_uom_qty
                new_price = line.price_unit

                if new_qty != original_qty or new_price != original_price:
                    products.append(line.name)
        
        if len(products) > 0:
            if sale_order.partner_id:
                order_url = sale_order._get_html_link(title=sale_order.name)
                message = f'Quantity and/or price for product(s) {', '.join(products)} \
                        on Quotation/Sale Order {order_url} have changed. \
                        New order total is {sale_order.amount_total}.'
            
                sale_order.partner_id.message_post(
                    body=message, 
                    subtype_xmlid='mail.mt_comment', 
                    body_is_html=True
                )

    @api.model
    def create(self, vals):
        sale_order = super(SaleOrder, self).create(vals)

        self._handle_create_new(sale_order)

        return sale_order
    
    def write(self, vals):
        # Get current state before updating the record
        sale_order = self
        original_state = sale_order.state

        original_lines = {}
        for line in sale_order.order_line:
            original_lines[line.id] = {'qty': line.product_uom_qty, 'price': line.price_unit, 'total': line.price_total}
        
        write_result = super(SaleOrder, self).write(vals)
        
        if 'state' in vals:
            self._handle_order_status_change(sale_order, original_state)

        if 'order_line' in vals:
            self._handle_order_lines_change(sale_order, original_lines)

        return write_result
    