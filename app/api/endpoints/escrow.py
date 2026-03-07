from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ...db.session import get_db
from ...models.marketplace import Escrow, Listing
from ...schemas.escrow import EscrowCreate, EscrowRead, EscrowUpdate

router = APIRouter()

@router.post("/init", response_model=EscrowRead)
def init_escrow(escrow_in: EscrowCreate, db: Session = Depends(get_db)):
    """
    Initiate an escrow transaction. Funds are presumed 'held' after this call.
    """
    # Verify listing exists
    listing = db.query(Listing).filter(Listing.id == escrow_in.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    db_escrow = Escrow(
        listing_id=escrow_in.listing_id,
        buyer_id=escrow_in.buyer_id,
        seller_id=escrow_in.seller_id,
        amount=escrow_in.amount,
        upi_ref=escrow_in.upi_ref,
        status="held"
    )
    db.add(db_escrow)
    db.commit()
    db.refresh(db_escrow)
    return db_escrow

@router.post("/{escrow_id}/confirm", response_model=EscrowRead)
def confirm_delivery(escrow_id: str, db: Session = Depends(get_db)):
    """
    Buyer confirms receipt of item. Release funds to seller.
    """
    db_escrow = db.query(Escrow).filter(Escrow.id == escrow_id).first()
    if not db_escrow:
        raise HTTPException(status_code=404, detail="Escrow not found")
    
    if db_escrow.status != "held":
        raise HTTPException(status_code=400, detail=f"Cannot confirm escrow in status: {db_escrow.status}")
    
    db_escrow.status = "released"
    db.commit()
    db.refresh(db_escrow)
    return db_escrow

@router.get("/user/{user_id}", response_model=List[EscrowRead])
def get_user_escrows(user_id: str, db: Session = Depends(get_db)):
    """
    Get all escrow transactions for a user (as buyer or seller).
    """
    return db.query(Escrow).filter((Escrow.buyer_id == user_id) | (Escrow.seller_id == user_id)).all()
