"""Emergency actions - FaceTime calls and iMessage."""

import logging
import platform
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


def call_facetime(phone: str) -> bool:
    """
    Initiate a FaceTime call.
    
    Args:
        phone: Phone number or Apple ID
        
    Returns:
        True if call was initiated successfully
    """
    if platform.system() != "Darwin":
        logger.warning("FaceTime is only available on macOS")
        return False
    
    try:
        # Clean phone number
        clean_phone = phone.replace(" ", "").replace("-", "")
        url = f"facetime://{clean_phone}"
        
        subprocess.run(["open", url], check=True)
        logger.info(f"FaceTime call initiated to {phone}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to initiate FaceTime call: {e}")
        return False
    except Exception as e:
        logger.error(f"Error initiating FaceTime: {e}")
        return False


def send_imessage(phone: str, message: str) -> bool:
    """
    Send an iMessage.
    
    Args:
        phone: Phone number or Apple ID
        message: Message text to send
        
    Returns:
        True if message was sent successfully
    """
    if platform.system() != "Darwin":
        logger.warning("iMessage is only available on macOS")
        return False
    
    try:
        # Escape message for AppleScript
        escaped_message = message.replace('"', '\\"').replace("'", "\\'")
        clean_phone = phone.replace(" ", "").replace("-", "")
        
        script = f'''
        tell application "Messages"
            set targetService to 1st account whose service type = iMessage
            set targetBuddy to participant "{clean_phone}" of targetService
            send "{escaped_message}" to targetBuddy
        end tell
        '''
        
        subprocess.run(
            ["osascript", "-e", script],
            check=True,
            capture_output=True,
        )
        logger.info(f"iMessage sent to {phone}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to send iMessage: {e}")
        # Try alternative method using buddy
        return _send_imessage_fallback(phone, message)
    except Exception as e:
        logger.error(f"Error sending iMessage: {e}")
        return False


def _send_imessage_fallback(phone: str, message: str) -> bool:
    """Fallback method to send iMessage."""
    try:
        escaped_message = message.replace('"', '\\"')
        clean_phone = phone.replace(" ", "").replace("-", "")
        
        script = f'''
        tell application "Messages"
            send "{escaped_message}" to buddy "{clean_phone}"
        end tell
        '''
        
        subprocess.run(
            ["osascript", "-e", script],
            check=True,
            capture_output=True,
        )
        logger.info(f"iMessage sent to {phone} (fallback method)")
        return True
    except Exception as e:
        logger.error(f"Fallback iMessage also failed: {e}")
        return False


def open_messages_app(phone: Optional[str] = None) -> bool:
    """
    Open the Messages app, optionally to a specific conversation.
    
    Args:
        phone: Optional phone number to open conversation with
        
    Returns:
        True if Messages was opened
    """
    if platform.system() != "Darwin":
        return False
    
    try:
        if phone:
            clean_phone = phone.replace(" ", "").replace("-", "")
            subprocess.run(["open", f"imessage://{clean_phone}"], check=True)
        else:
            subprocess.run(["open", "-a", "Messages"], check=True)
        return True
    except Exception as e:
        logger.error(f"Failed to open Messages: {e}")
        return False


