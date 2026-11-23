from flask import Blueprint, request, jsonify
from ..models import db, Hotel, Itinerary, BookingInquiry, User, SystemSetting
from ..services.auth_service import token_required, roles_required
from ..services.analytics_service import AnalyticsService

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/dashboard', methods=['GET'])
@roles_required(['admin'])
def get_dashboard_data(current_user):
    """Retrieves executive financial KPIs, charts, and administrative analytics (Admin Only)"""
    summary = AnalyticsService.get_dashboard_summary()
    return jsonify({
        'success': True,
        'user_role': current_user.role,
        **summary
    })

@admin_bp.route('/agent-summary', methods=['GET'])
@roles_required(['employee', 'admin'])
def get_agent_summary(current_user):
    """Retrieves client travel bookings and inquiry queue for Travel Agents"""
    inquiries = BookingInquiry.query.order_by(BookingInquiry.created_at.desc()).all()
    pending = [inq for inq in inquiries if inq.status == 'Pending']
    in_review = [inq for inq in inquiries if inq.status == 'In Review']
    confirmed = [inq for inq in inquiries if inq.status == 'Confirmed']

    return jsonify({
        'success': True,
        'user_role': current_user.role,
        'stats': {
            'total_inquiries': len(inquiries),
            'pending_count': len(pending),
            'in_review_count': len(in_review),
            'confirmed_count': len(confirmed)
        },
        'inquiries': [inq.to_dict() for inq in inquiries]
    })

# ----------------- PARTNER HOTEL MANAGEMENT (CRUD) -----------------

@admin_bp.route('/hotels', methods=['GET'])
@roles_required(['admin'])
def list_hotels(current_user):
    hotels = Hotel.query.order_by(Hotel.created_at.desc()).all()
    return jsonify({
        'success': True,
        'count': len(hotels),
        'hotels': [h.to_dict() for h in hotels]
    })

@admin_bp.route('/hotels', methods=['POST'])
@roles_required(['admin'])
def create_hotel(current_user):
    data = request.get_json() or {}
    
    name = data.get('name', '').strip()
    city = data.get('city', '').strip()
    country = data.get('country', '').strip()
    address = data.get('address', '').strip()
    standard_rate = float(data.get('standard_rate_per_night', 150.0))
    partner_discount = float(data.get('partner_discount_percent', 15.0))
    jbd_commission = float(data.get('jbd_commission_percent', 12.0))
    stars = int(data.get('stars', 4))
    description = data.get('description', 'Luxury accommodations with modern amenities.')
    image_url = data.get('image_url', 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600')
    is_partner = data.get('is_partner', True)
    amenities = data.get('amenities', ['Free WiFi', 'Breakfast Included', 'Swimming Pool'])
    room_types = data.get('room_types', [{'name': 'Standard King', 'price_multiplier': 1.0}])
    nearby = data.get('nearby_attractions', [])
    dest_id = data.get('destination_id', None)

    if not name or not city or not country:
        return jsonify({'success': False, 'message': 'Hotel name, city and country are required.'}), 400

    hotel = Hotel(
        destination_id=dest_id,
        name=name,
        city=city,
        country=country,
        address=address or f"{city} Downtown Boulevard",
        stars=stars,
        description=description,
        image_url=image_url,
        standard_rate_per_night=standard_rate,
        is_partner=is_partner,
        partner_discount_percent=partner_discount,
        jbd_commission_percent=jbd_commission
    )
    hotel.set_amenities_list(amenities)
    hotel.set_room_types_list(room_types)
    hotel.set_nearby_attractions_list(nearby)

    db.session.add(hotel)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Partner hotel "{hotel.name}" created successfully.',
        'hotel': hotel.to_dict()
    }), 201

@admin_bp.route('/hotels/<int:hotel_id>', methods=['PUT'])
@roles_required(['admin'])
def update_hotel(current_user, hotel_id):
    hotel = Hotel.query.get_or_404(hotel_id)
    data = request.get_json() or {}

    if 'name' in data:
        hotel.name = data['name'].strip()
    if 'city' in data:
        hotel.city = data['city'].strip()
    if 'country' in data:
        hotel.country = data['country'].strip()
    if 'address' in data:
        hotel.address = data['address'].strip()
    if 'stars' in data:
        hotel.stars = int(data['stars'])
    if 'description' in data:
        hotel.description = data['description']
    if 'image_url' in data:
        hotel.image_url = data['image_url']
    if 'standard_rate_per_night' in data:
        hotel.standard_rate_per_night = float(data['standard_rate_per_night'])
    if 'is_partner' in data:
        hotel.is_partner = bool(data['is_partner'])
    if 'partner_discount_percent' in data:
        hotel.partner_discount_percent = float(data['partner_discount_percent'])
    if 'jbd_commission_percent' in data:
        hotel.jbd_commission_percent = float(data['jbd_commission_percent'])
    if 'amenities' in data:
        hotel.set_amenities_list(data['amenities'])
    if 'room_types' in data:
        hotel.set_room_types_list(data['room_types'])
    if 'nearby_attractions' in data:
        hotel.set_nearby_attractions_list(data['nearby_attractions'])
    if 'is_active' in data:
        hotel.is_active = bool(data['is_active'])

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Hotel "{hotel.name}" updated successfully.',
        'hotel': hotel.to_dict()
    })

@admin_bp.route('/hotels/<int:hotel_id>', methods=['DELETE'])
@roles_required(['admin'])
def delete_hotel(current_user, hotel_id):
    hotel = Hotel.query.get_or_404(hotel_id)
    name = hotel.name
    db.session.delete(hotel)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Hotel "{name}" deleted successfully.'
    })

# ----------------- CUSTOMER TRAVEL PLANS & INQUIRIES -----------------

@admin_bp.route('/inquiries', methods=['GET'])
@roles_required(['employee', 'admin'])
def list_inquiries(current_user):
    inquiries = BookingInquiry.query.order_by(BookingInquiry.created_at.desc()).all()
    return jsonify({
        'success': True,
        'count': len(inquiries),
        'inquiries': [inq.to_dict() for inq in inquiries]
    })

@admin_bp.route('/inquiries/<int:inquiry_id>', methods=['PUT'])
@roles_required(['employee', 'admin'])
def update_inquiry(current_user, inquiry_id):
    inquiry = BookingInquiry.query.get_or_404(inquiry_id)
    data = request.get_json() or {}

    if 'status' in data:
        inquiry.status = data['status']
        if inquiry.itinerary:
            inquiry.itinerary.status = data['status']
    if 'assigned_employee_id' in data:
        inquiry.assigned_employee_id = int(data['assigned_employee_id']) if data['assigned_employee_id'] else None
    if 'agent_notes' in data:
        inquiry.agent_notes = data['agent_notes']
    if 'quote_amount' in data:
        inquiry.quote_amount = float(data['quote_amount'])
    if 'discount_applied' in data:
        inquiry.discount_applied = float(data['discount_applied'])
    if 'commission_earned' in data:
        inquiry.commission_earned = float(data['commission_earned'])

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Booking inquiry #{inquiry.id} updated.',
        'inquiry': inquiry.to_dict()
    })

# ----------------- SETTINGS & COMMISSION CONFIGURATION -----------------

@admin_bp.route('/settings', methods=['GET'])
@roles_required(['employee', 'admin'])
def get_settings(current_user):
    settings = SystemSetting.query.all()
    settings_dict = {s.key: s.value for s in settings}
    return jsonify({
        'success': True,
        'settings': settings_dict
    })

@admin_bp.route('/settings', methods=['PUT'])
@roles_required(['admin'])
def update_settings(current_user):
    data = request.get_json() or {}
    
    for key, val in data.items():
        SystemSetting.set_value(key, val)

    return jsonify({
        'success': True,
        'message': 'System settings updated successfully.'
    })
