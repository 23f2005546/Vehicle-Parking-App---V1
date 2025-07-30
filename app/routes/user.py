from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import ParkingLot, ParkingSpot, Reservation
from app.extensions import db

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
    reservation = Reservation.query.filter_by(user_id=current_user.id).first()
    return render_template('user/my_reservation.html', user=current_user, reservation=reservation)

@user_bp.route('/lot/<int:lot_id>')
@login_required
def view_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').all()
    return render_template('user/lot_detail.html', lot=lot, available_spots=available_spots)

@user_bp.route('/lot/<int:lot_id>/reserve/<int:spot_id>', methods=['POST'])
@login_required
def reserve_spot(lot_id, spot_id):
    existing_reservation = Reservation.query.filter_by(user_id=current_user.id).first()
    if existing_reservation:
        flash("You already have a reservation.")
        return redirect(url_for('user.my_reservation'))

    spot = ParkingSpot.query.get_or_404(spot_id)
    if spot.status != 'A':
        flash("Spot is already taken.")
        return redirect(url_for('user.view_lot', lot_id=lot_id))

    spot.status = 'O'
    new_reservation = Reservation(
        spot_id=spot.id,
        user_id=current_user.id,
        cost_per_unit=spot.lot.price
    )
    db.session.add(new_reservation)
    db.session.commit()
    flash("Reservation successful.")
    return redirect(url_for('user.my_reservation'))

@user_bp.route('/cancel-reservation', methods=['POST'])
@login_required
def cancel_reservation():
    reservation = Reservation.query.filter_by(user_id=current_user.id).first()
    if reservation:
       
        reservation.spot.status = 'A'

        db.session.delete(reservation)
        db.session.commit()
        flash("Reservation cancelled successfully.")
    else:
        flash("No reservation found to cancel.")

    return redirect(url_for('user.dashboard'))