from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from ...db.session import get_db
from ...models.chat import Conversation, Message
from ...models.user import User
from ...schemas.chat import (
    ConversationRead, 
    MessageRead, 
    MessageCreate,
    UserBasic
)
from ...api.deps import get_current_user

router = APIRouter()

# Helper to get sio instance from app
def get_sio():
    from ..main import app
    return app.sio

@router.get("/conversations", response_model=List[ConversationRead])
def get_conversations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversations = db.query(Conversation).filter(
        (Conversation.participant_one_id == current_user.id) | 
        (Conversation.participant_two_id == current_user.id)
    ).order_by(Conversation.updated_at.desc()).all()
    
    result = []
    for conv in conversations:
        other_user_id = conv.participant_two_id if conv.participant_one_id == current_user.id else conv.participant_one_id
        other_user = db.query(User).filter(User.id == other_user_id).first()
        
        last_msg = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at.desc()).first()
        
        result.append({
            "id": conv.id,
            "participant_one_id": conv.participant_one_id,
            "participant_two_id": conv.participant_two_id,
            "listing_id": conv.listing_id,
            "property_id": conv.property_id,
            "last_message": last_msg.content if last_msg else None,
            "updated_at": conv.updated_at,
            "other_user": {
                "id": other_user.id,
                "first_name": other_user.first_name,
                "last_name": other_user.last_name,
                "profile_pic_url": other_user.profile_pic_url,
                "last_seen": other_user.last_seen
            }
        })
    return result

@router.get("/messages/{conversation_id}", response_model=List[MessageRead])
def get_messages(conversation_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conv.participant_one_id != current_user.id and conv.participant_two_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()
    return messages

@router.post("/messages", response_model=MessageRead)
async def send_message(msg_in: MessageCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == msg_in.conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    message = Message(
        conversation_id=msg_in.conversation_id,
        sender_id=current_user.id,
        content=msg_in.content
    )
    db.add(message)
    conv.updated_at = message.created_at
    db.commit()
    db.refresh(message)
    
    # Broadcast message via Socket.io
    try:
        sio = get_sio()
        msg_data = {
            "id": str(message.id),
            "conversation_id": str(message.conversation_id),
            "sender_id": str(message.sender_id),
            "content": str(message.content),
            "created_at": message.created_at.isoformat()
        }
        # Send to all connected to this conversation room
        await sio.emit('new_message', msg_data, room=msg_in.conversation_id)
        print(f"Broadcasted message to room {msg_in.conversation_id}")
    except Exception as e:
        print(f"Error broadcasting message: {e}")
        
    return message

@router.post("/start", response_model=ConversationRead)
def start_conversation(
    other_user_id: str, 
    listing_id: str = None, 
    property_id: str = None, 
    initial_message: str = None,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # Verify other_user exists
    other_user = db.query(User).filter(User.id == other_user_id).first()
    if not other_user:
        raise HTTPException(status_code=404, detail="Other user not found")

    # Check if conversation already exists between these two users (ignore listing for merging)
    conv = db.query(Conversation).filter(
        ((Conversation.participant_one_id == current_user.id) & (Conversation.participant_two_id == other_user_id)) |
        ((Conversation.participant_one_id == other_user_id) & (Conversation.participant_two_id == current_user.id))
    ).first()
    
    if not conv:
        conv = Conversation(
            participant_one_id=current_user.id,
            participant_two_id=other_user_id,
            listing_id=listing_id,
            property_id=property_id
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
    else:
        # If it exists, update the listing context to the current one if provided
        if listing_id:
            conv.listing_id = listing_id
            db.commit()

    # Send initial message if provided
    if initial_message:
        # Check if the last message in this conversation is identical and recent to avoid duplication
        last_m = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at.desc()).first()
        if not last_m or last_m.content != initial_message:
            msg = Message(
                conversation_id=conv.id,
                sender_id=current_user.id,
                content=initial_message
            )
            db.add(msg)
            conv.updated_at = datetime.utcnow()
            db.commit()
        
    # Refresh to get latest state
    db.refresh(conv)
    last_msg = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at.desc()).first()
    
    return {
        "id": conv.id,
        "participant_one_id": conv.participant_one_id,
        "participant_two_id": conv.participant_two_id,
        "listing_id": conv.listing_id,
        "property_id": conv.property_id,
        "last_message": last_msg.content if last_msg else None,
        "updated_at": conv.updated_at,
        "other_user": {
            "id": other_user.id,
            "first_name": other_user.first_name,
            "last_name": other_user.last_name,
            "profile_pic_url": other_user.profile_pic_url,
            "last_seen": other_user.last_seen
        }
    }
