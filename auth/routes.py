from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db
from models import User
from forms import RegisterForm, LoginForm
from utils import superadmin_required


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data.lower()).first()

        if existing_user:
            flash("Email already registered.", "danger")
            return redirect(url_for("auth.register"))

        user = User(
            full_name=form.full_name.data,
            email=form.email.data.lower(),
            role="user"
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()

        if not user or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        if not user.is_active_account:
            flash("Your account has been disabled.", "danger")
            return redirect(url_for("auth.login"))

        login_user(user)

        next_page = request.args.get("next")
        return redirect(next_page or url_for("dashboard"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/users")
@login_required
@superadmin_required
def users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("auth/users.html", users=users)


@auth_bp.route("/users/<int:user_id>/role/<role>", methods=["POST"])
@login_required
@superadmin_required
def update_role(user_id, role):
    user = User.query.get_or_404(user_id)

    if role not in ["user", "admin", "superadmin"]:
        flash("Invalid role selected.", "danger")
        return redirect(url_for("auth.users"))

    user.role = role
    db.session.commit()

    flash("User role updated successfully.", "success")
    return redirect(url_for("auth.users"))