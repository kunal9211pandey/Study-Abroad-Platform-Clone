import os
import stripe
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Payment, Application, db, PaymentStatus
from datetime import datetime

payments = Blueprint('payments', __name__)

# Initialize Stripe (you'll add your STRIPE_SECRET_KEY later)
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_placeholder')

def get_domain():
    """Get the domain for Stripe redirects"""
    if os.environ.get('REPLIT_DEPLOYMENT'):
        return f"https://{os.environ.get('REPL_SLUG')}.{os.environ.get('REPLIT_CLUSTER')}.replit.dev"
    else:
        return "http://localhost:5000"

@payments.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Create a Stripe checkout session for application fee payment"""
    try:
        application_id = request.form.get('application_id')
        application = Application.query.get_or_404(application_id)
        
        # Verify user owns this application
        if application.user_id != current_user.id:
            flash('Access denied.', 'error')
            return redirect(url_for('dashboard'))
        
        # Check if payment already exists
        existing_payment = Payment.query.filter_by(
            application_id=application_id,
            status=PaymentStatus.COMPLETED
        ).first()
        
        if existing_payment:
            flash('Payment already completed for this application.', 'info')
            return redirect(url_for('view_application', application_id=application_id))
        
        # Get application fee from institution
        amount = float(application.institution.application_fee)
        
        if amount <= 0:
            flash('No payment required for this application.', 'info')
            return redirect(url_for('view_application', application_id=application_id))
        
        # Create payment record
        payment = Payment(
            user_id=current_user.id,
            application_id=application_id,
            amount=amount,
            currency='USD',
            description=f'Application fee for {application.program.name} at {application.institution.name}',
            status=PaymentStatus.PENDING
        )
        db.session.add(payment)
        db.session.commit()
        
        # Create Stripe checkout session
        YOUR_DOMAIN = get_domain()
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'Application Fee - {application.institution.name}',
                        'description': f'{application.program.name}',
                    },
                    'unit_amount': int(amount * 100),  # Stripe uses cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=YOUR_DOMAIN + f'/payments/success?session_id={{CHECKOUT_SESSION_ID}}&payment_id={payment.id}',
            cancel_url=YOUR_DOMAIN + f'/payments/cancel?payment_id={payment.id}',
            metadata={
                'payment_id': payment.id,
                'application_id': application_id,
                'user_id': current_user.id
            }
        )
        
        # Update payment with Stripe session ID
        payment.stripe_payment_intent_id = checkout_session.id
        db.session.commit()
        
        return redirect(checkout_session.url, code=303)
        
    except stripe.error.StripeError as e:
        flash(f'Payment processing error: {str(e)}', 'error')
        return redirect(url_for('dashboard'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while processing payment.', 'error')
        print(f"Payment error: {e}")
        return redirect(url_for('dashboard'))

@payments.route('/success')
@login_required
def payment_success():
    """Handle successful payment"""
    session_id = request.args.get('session_id')
    payment_id = request.args.get('payment_id')
    
    if not session_id or not payment_id:
        flash('Invalid payment session.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Verify payment with Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            # Update payment status
            payment = Payment.query.get(payment_id)
            if payment and payment.user_id == current_user.id:
                payment.status = PaymentStatus.COMPLETED
                payment.completed_at = datetime.utcnow()
                payment.stripe_metadata = str(session)
                db.session.commit()
                
                flash('Payment successful! Your application has been submitted.', 'success')
                return render_template('payments/success.html', payment=payment)
        
        flash('Payment verification failed.', 'error')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash('Error verifying payment.', 'error')
        print(f"Payment verification error: {e}")
        return redirect(url_for('dashboard'))

@payments.route('/cancel')
@login_required
def payment_cancel():
    """Handle cancelled payment"""
    payment_id = request.args.get('payment_id')
    
    if payment_id:
        payment = Payment.query.get(payment_id)
        if payment and payment.user_id == current_user.id:
            payment.status = PaymentStatus.FAILED
            db.session.commit()
    
    flash('Payment was cancelled.', 'info')
    return render_template('payments/cancel.html')

@payments.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        # In production, verify webhook signature
        # event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        
        # For now, parse the event directly
        import json
        event = json.loads(payload)
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            payment_id = session['metadata'].get('payment_id')
            
            if payment_id:
                payment = Payment.query.get(payment_id)
                if payment:
                    payment.status = PaymentStatus.COMPLETED
                    payment.completed_at = datetime.utcnow()
                    db.session.commit()
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 400

@payments.route('/history')
@login_required
def payment_history():
    """View payment history for current user"""
    payments = Payment.query.filter_by(user_id=current_user.id).order_by(
        Payment.created_at.desc()
    ).all()
    
    return render_template('payments/history.html', payments=payments)

@payments.route('/refund/<int:payment_id>', methods=['POST'])
@login_required
def request_refund(payment_id):
    """Request a refund for a payment"""
    payment = Payment.query.get_or_404(payment_id)
    
    # Verify user owns this payment
    if payment.user_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('payments.payment_history'))
    
    if payment.status != PaymentStatus.COMPLETED:
        flash('Only completed payments can be refunded.', 'error')
        return redirect(url_for('payments.payment_history'))
    
    try:
        # In production, process actual Stripe refund
        # refund = stripe.Refund.create(
        #     payment_intent=payment.stripe_payment_intent_id,
        #     amount=int(payment.amount * 100)
        # )
        
        # For now, just update status
        payment.status = PaymentStatus.REFUNDED
        db.session.commit()
        
        flash('Refund request submitted successfully.', 'success')
        
    except Exception as e:
        flash('Error processing refund request.', 'error')
        print(f"Refund error: {e}")
    
    return redirect(url_for('payments.payment_history'))

# API endpoints for payment status
@payments.route('/api/payment-status/<int:payment_id>')
@login_required
def get_payment_status(payment_id):
    """Get payment status via API"""
    payment = Payment.query.get_or_404(payment_id)
    
    if payment.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'id': payment.id,
        'status': payment.status.value,
        'amount': float(payment.amount),
        'currency': payment.currency,
        'created_at': payment.created_at.isoformat(),
        'completed_at': payment.completed_at.isoformat() if payment.completed_at else None
    })