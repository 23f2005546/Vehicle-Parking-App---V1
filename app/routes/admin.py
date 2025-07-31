from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import ParkingLot, ParkingSpot, Reservation

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        return "Access denied", 403

    lots = ParkingLot.query.all()
    return render_template('admin/dashboard.html', user=current_user, lots=lots)


@admin_bp.route('/create_lot', methods=['GET', 'POST'])
@login_required
def create_lot():
    if not current_user.is_admin:
        return "Access denied", 403

    if request.method == 'POST':
        name = request.form.get('prime_location_name')
        price = request.form.get('price')
        address = request.form.get('address')
        pin_code = request.form.get('pin_code')
        max_spots = int(request.form.get('max_spots', 0))

        new_lot = ParkingLot(
            prime_location_name=name,
            price=price,
            address=address,
            pin_code=pin_code,
            max_spots=max_spots
        )
        db.session.add(new_lot)
        db.session.flush()  # ensure lot ID is available

        for i in range(1, max_spots + 1):
            spot = ParkingSpot(lot_id=new_lot.id, spot_number=i, is_available=True)
            db.session.add(spot)

        db.session.commit()
        flash("Parking lot and spots added successfully.")
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/create_lot.html')


@admin_bp.route('/reservations')
@login_required
def view_all_reservations():
    if not current_user.is_admin:
        return "Unauthorized", 403

    reservations = Reservation.query.order_by(Reservation.parking_time.desc()).all()
    return render_template('admin/all_reservations.html', reservations=reservations)
