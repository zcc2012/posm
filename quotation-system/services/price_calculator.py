def calculate_subtotal(quantity, unit_price):
    return (quantity or 0) * (unit_price or 0)


def calculate_material_unit_price(material, length, width, fallback_unit_price=0):
    if not material:
        return fallback_unit_price or 0
    base_price = material[0] or 0
    square_price = material[1] or 0
    area_in_square_meters = ((length or 0) * (width or 0)) / 1000000
    return base_price + (area_in_square_meters * square_price)


def refresh_quotation_total(cursor, quotation_id):
    cursor.execute('SELECT SUM(subtotal) FROM quotation_items WHERE quotation_id=?', (quotation_id,))
    total_amount = cursor.fetchone()[0] or 0
    cursor.execute('UPDATE quotations SET total_amount=? WHERE id=?', (total_amount, quotation_id))
    return total_amount
