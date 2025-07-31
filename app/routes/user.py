from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from app.models import ParkingLot, ParkingSpot, Reservation
from app.extensions import db

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return "Admins aren't allowed here.", 403
    lots = ParkingLot.query.all()
    return render_template('user/dashboard.html', user=current_user, lots=lots)

@user_bp.route('/my-reservation')
@login_required
def my_reservation():
    all_reservations = Reservation.query.filter_by(user_id=current_user.id).all()
    return render_template('user/my_reservation.html', reservations=all_reservations)

@user_bp.route('/lot/<int:lot_id>')
@login_required
def view_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    available = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').all()
    return render_template('user/lot_detail.html', lot=lot, available_spots=available)

@user_bp.route('/lot/<int:lot_id>/reserve/<int:spot_id>', methods=['POST'])
@login_required
def reserve_spot(lot_id, spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    if spot.status != 'A':
        flash("This spot is no longer available.")
        return redirect(url_for('user.view_lot', lot_id=lot_id))

    spot.status = 'O'
    spot.is_available = False

    res = Reservation(
        user_id=current_user.id,
        spot_id=spot.id,
        cost_per_unit=spot.lot.price,
        parking_time=datetime.now()
    )
    db.session.add(res)
    db.session.commit()

    flash("Spot reserved.")
    return redirect(url_for('user.my_reservation'))

@user_bp.route('/leave/<int:reservation_id>', methods=['POST'])
@login_required
def leave_parking(reservation_id):
    res = Reservation.query.get_or_404(reservation_id)
    if res.user_id != current_user.id or res.leaving_time is not None:
        flash("Invalid reservation.")
        return redirect(url_for('user.my_reservation'))

    res.leaving_time = datetime.now()
    res.spot.status = 'A'
    res.spot.is_available = True
    db.session.commit()

    flash("You left the parking spot.")
    return redirect(url_for('user.my_reservation'))

@user_bp.route('/cancel/<int:reservation_id>', methods=['POST'])
@login_required
def cancel_reservation(reservation_id):
    res = Reservation.query.get_or_404(reservation_id)
    if res.user_id != current_user.id or res.leaving_time is not None:
        flash("Can't cancel this reservation.")
        return redirect(url_for('user.my_reservation'))

    res.spot.status = 'A'
    res.spot.is_available = True
    db.session.delete(res)
    db.session.commit()

    flash("Reservation cancelled.")
    return redirect(url_for('user.my_reservation'))
