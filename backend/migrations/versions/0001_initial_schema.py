"""Create initial CatchMe schema."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("sex", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("date_joined", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("profiles",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("goal", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_name", sa.String(32), nullable=False, server_default=""),
        sa.Column("last_name", sa.String(32), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("city", sa.String(120)), sa.Column("height", sa.Integer()),
        sa.Column("weight", sa.Integer()), sa.Column("avatar", sa.String(500)),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"))
    op.create_table("climbing",
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("leading", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("where_leading", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bouldering", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("where_bouldering", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("speed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("alpinism", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("belay", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("belay_description", sa.Text(), nullable=False, server_default=""),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("profile_id"))
    op.create_table("chats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.create_table("chat_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("joined", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("chat_id", "user_id", name="uq_chat_members_chat_id_user_id"))
    op.create_table("messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("text", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"))
    op.create_index("ix_messages_chat_id", "messages", ["chat_id"])

def downgrade():
    op.drop_index("ix_messages_chat_id", table_name="messages")
    op.drop_table("messages")
    op.drop_table("chat_members")
    op.drop_table("chats")
    op.drop_table("climbing")
    op.drop_table("profiles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
