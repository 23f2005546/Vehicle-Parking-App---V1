from flask import Blueprint, render_template, redirect, url_for, request, flash, make_response
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User, Reservation, ParkingLot, ParkingSpot
import csv
from io import StringIO

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        return "Access denied", 403
    lots = ParkingLot.query.all()
    return render_template('admin/dashboard.html', lots=lots, user=current_user)

@admin_bp.route('/reservations')
@login_required
def view_all_reservations():
    if not current_user.is_admin:
        return "Unauthorized", 403
    reservations = Reservation.query.order_by(Reservation.parking_time.desc()).all()
    return render_template('admin/all_reservations.html', reservations=reservations)

@admin_bp.route('/download-reservations')
@login_required
def download_reservations():
    if not current_user.is_admin:
        return "Unauthorized", 403

    reservations = Reservation.query.order_by(Reservation.parking_time.desc()).all()
    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(['Reservation ID', 'Username', 'Full Name', 'Lot', 'Spot ID', 'Start Time', 'End Time', 'Cost'])

    for r in reservations:
        writer.writerow([
            r.id,
            r.user.username,
            r.user.full_name,
            r.spot.lot.prime_location_name,
            r.spot.id,
            r.parking_time.strftime('%Y-%m-%d %H:%M'),
            r.leaving_time.strftime('%Y-%m-%d %H:%M') if r.leaving_time else '',
            r.cost_per_unit
        ])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=all_reservations.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@admin_bp.route('/create_lot', methods=['GET', 'POST'])
@login_required
def create_lot():
    if not current_user.is_admin:
        return "Access denied", 403

    if request.method == 'POST':
        lot_name = request.form.get('prime_location_name')
        price = request.form.get('price')
        address = request.form.get('address')
        pin_code = request.form.get('pin_code')

        try:
            max_spots = int(request.form.get('max_spots'))
        except (ValueError, TypeError):
            flash('Invalid number of spots.')
            return redirect(url_for('admin.create_lot'))

        new_lot = ParkingLot(
            prime_location_name=lot_name,
            price=price,
            address=address,
            pin_code=pin_code,
            max_spots=max_spots
        )
        db.session.add(new_lot)
        db.session.commit()

        for num in range(1, max_spots + 1):
            spot = ParkingSpot(
                lot_id=new_lot.id,
                spot_number=num,
                is_available=True,
                status='A'
            )
            db.session.add(spot)

        db.session.commit()
        flash('Lot and its spots added.')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/create_lot.html')

@admin_bp.route('/delete-reservation/<int:reservation_id>', methods=['POST'])
@login_required
def delete_reservation(reservation_id):
    if not current_user.is_admin:
        return "Unauthorized", 403

    reservation = Reservation.query.get_or_404(reservation_id)

    reservation.spot.is_available = True
    reservation.spot.status = 'A'

    db.session.delete(reservation)
    db.session.commit()

    flash('Reservation removed.')
    return redirect(url_for('admin.view_all_reservations'))

@admin_bp.route('/users')
@login_required
def view_users():
    if not current_user.is_admin:
        return "Unauthorized access", 403

    all_users = User.query.filter_by(is_admin=False).all()
    user_data = []

    for user in all_users:
        active_res = Reservation.query.filter_by(user_id=user.id, leaving_time=None).first()
        user_data.append({
            'user': user,
            'reservation': active_res
        })

    return render_template('admin/user_list.html', users_data=user_data)

@admin_bp.route('/delete_lot/<int:lot_id>', methods=['POST'])
@login_required
def delete_lot(lot_id):
    if not current_user.is_admin:
        return "Unauthorized", 403

    lot = ParkingLot.query.get_or_404(lot_id)

    for spot in lot.spots:
        Reservation.query.filter_by(spot_id=spot.id).delete()
        db.session.delete(spot)

    db.session.delete(lot)
    db.session.commit()

    flash('Entire lot and reservations removed.')
    return redirect(url_for('admin.dashboard'))
