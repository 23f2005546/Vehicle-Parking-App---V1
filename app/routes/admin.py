from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models import ParkingLot, ParkingSpot

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        return "Access denied", 403

    lots = ParkingLot.query.all()
    return render_template('admin/dashboard.html', user=current_user, lots=lots)

@admin_bp.route('/reservations')
@login_required
def all_reservations():
    if not current_user.is_admin:
        return "Access denied", 403

    from app.models import Reservation 
    reservations = Reservation.query.all()
    return render_template('admin/all_reservations.html', reservations=reservations)


@admin_bp.route('/create_lot', methods=['GET', 'POST'])
@login_required
def create_lot():
    if not current_user.is_admin:
        return "Access denied", 403

    if request.method == 'POST':
        name = request.form['prime_location_name']
        price = request.form['price']
        address = request.form['address']
        pin_code = request.form['pin_code']
        max_spots = int(request.form['max_spots'])

        new_lot = ParkingLot(
            prime_location_name=name,
            price=price,
            address=address,
            pin_code=pin_code,
            max_spots=max_spots
        )
        db.session.add(new_lot)
        db.session.commit()

        for i in range(1, max_spots + 1):
            spot = ParkingSpot(lot_id=new_lot.id, spot_number=i, is_available=True)
            db.session.add(spot)

        db.session.commit()
        flash('Parking lot created with spots.')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/create_lot.html')
