from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import ParkingLot, ParkingSpot, Reservation
from app.extensions import db
from datetime import datetime

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return "Admins can't access this", 403
    lots = ParkingLot.query.all()
    return render_template('user/dashboard.html', user=current_user, lots=lots)


@user_bp.route('/my-reservation')
@login_required
def my_reservation():
    reservations = Reservation.query.filter_by(user_id=current_user.id).all()

    results = []
    for res in reservations:
        cost = None
        if res.leaving_time:
            duration = (res.leaving_time - res.parking_time).total_seconds() / 3600
            cost = round(duration * res.cost_per_unit, 2)
        results.append((res, cost))

    return render_template('user/my_reservation.html', reservations=results)



@user_bp.route('/lot/<int:lot_id>')
@login_required
def view_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    free_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').all()
    return render_template('user/lot_detail.html', lot=lot, available_spots=free_spots)


@user_bp.route('/lot/<int:lot_id>/reserve/<int:spot_id>', methods=['POST'])
@login_required
def reserve_spot(lot_id, spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)

    if spot.status != 'A':
        flash("Spot is already taken.")
        return redirect(url_for('user.view_lot', lot_id=lot_id))

    spot.status = 'O'
    spot.is_available = False

    new_reservation = Reservation(
        spot_id=spot.id,
        user_id=current_user.id,
        cost_per_unit=spot.lot.price
    )
    db.session.add(new_reservation)
    db.session.commit()

    flash("Reservation successful.")
    return redirect(url_for('user.my_reservation'))



@user_bp.route('/leave', methods=['POST'])
@login_required
def leave_parking():
    reservation_id = request.form.get('reservation_id')
    reservation = Reservation.query.filter_by(id=reservation_id, user_id=current_user.id, leaving_time=None).first()

    if not reservation:
        flash("Invalid reservation or already left.")
        return redirect(url_for('user.my_reservation'))

    reservation.leaving_time = datetime.utcnow()
    db.session.commit()

    flash("You have left the parking spot.")
    return redirect(url_for('user.my_reservation'))



@user_bp.route('/cancel', methods=['POST'])
@login_required
def cancel_reservation():
    reservation_id = request.form.get('reservation_id')
    reservation = Reservation.query.filter_by(id=reservation_id, user_id=current_user.id, leaving_time=None).first()

    if not reservation:
        flash("No active reservation found to cancel.")
        return redirect(url_for('user.my_reservation'))

    spot = reservation.spot
    spot.status = 'A'
    spot.is_available = True

    db.session.delete(reservation)
    db.session.commit()

    flash("Reservation cancelled successfully.")
    return redirect(url_for('user.my_reservation'))

