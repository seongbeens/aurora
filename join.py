from telegram.ext import ConversationHandler, CallbackQueryHandler, Filters
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

# Import PKG
from api import *

# Enable Logging
convLogger = logging.getLogger(__name__)
convLogger.addHandler(ConvLogHandler)

errorLogger = logging.getLogger(__name__)
errorLogger.addHandler(ErrorLogHandler)


#################### DEF: PRIVACY AGREEMENT ####################

def privacyAgreement(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '*개인정보 수집 및 이용 동의*\n'\
          + '\'테슬라 오로라\'는 텔레그램 메신저를 통한 Tesla 차량의 편리한 통제 및 자동화 기능을 구현하는 봇(Bot)입니다.\n'\
          + '\'테슬라 오로라\'는 아래의 목적으로 개인정보를 수집 및 이용하며, 회원의 개인정보를 안전하게 취급하는데 최선을 다할 것입니다.\n\n'\
          + '[[개인정보 수집 및 이용에 대한 안내]]\n'\
          + '1. 목적 : 이용자 개인 식별, 서비스 이용 의사 확인, 서비스 공지사항 안내, Tesla 계정 연동, 서비스 제공\n'\
          + '2. 항목 : 전화번호, 이메일 주소, Tesla 계정의 OAuth Token, 차량의 세부 정보(제원, 상태, 위치 정보 등), Telegram 사용자 이름 및 고유번호\n'\
          + '3. 보유기간 : 회원 탈퇴 시까지 보유\n\n'\
          + '위 개인정보 수집에 대한 동의를 거부할 권리가 있으며, 동의하지 않으실 경우 서비스 제공이 불가하여 가입이 제한됩니다.'
  keyboard = [['네, 동의합니다.'], ['동의하지 않습니다.']]

  reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
  update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

  return JOIN_AGREEMENT

def privacyDisagree(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '소중한 개인정보를 위한 선택을 존중합니다.\n다음 기회에 다시 찾아뵙기를 희망합니다.'
  update.message.reply_text(message, reply_markup = ReplyKeyboardRemove())

  return ConversationHandler.END


#################### DEF: GET PRIVACY INFO. ####################

def getName(update, context):
  # Write Privacy info.
  if sql.createAccount(update.message.chat_id):
    # Logging Conversation
    convLog(update, convLogger)

    # Message
    message = '이제 본격적인 가입 절차를 진행할게요!\U0001F917\n'\
            + '잘못 입력하신 항목이 있다면 가입 완료 후 계정 설정에서 수정할 수 있으니 끝까지 가입을 완료해주세요:)'
    update.message.reply_text(message, parse_mode = 'Markdown', reply_markup = ReplyKeyboardRemove())

    message = '*닉네임을 입력해주세요.*\n닉네임은 한글로 2~8자만 입력할 수 있습니다.'
    update.message.reply_text(message, parse_mode = 'Markdown', reply_markup = ReplyKeyboardRemove())

    return JOIN_GET_NAME

  else: return getName(update, context)

def incorrect_getName(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '닉네임은 한글로 2~8자만 입력할 수 있어요\U0001F635\n*닉네임을 입력해주세요.*'
  update.message.reply_text(message, parse_mode = 'Markdown')

  return JOIN_GET_NAME

def getPhone(update, context):
  # Write Privacy info.
  if sql.modifyAccount(update.message.chat_id, ['nickname'], [update.message.text]):
    # Logging Conversation
    convLog(update, convLogger)

    # Message
    message = '*전화번호를 입력해주세요.*\n전화번호는 대시(-)를 제외하고 입력해주세요.'
    update.message.reply_text(message, parse_mode = 'Markdown')

    return JOIN_GET_PHONE
    
  else: return getPhone(update, context)

def incorrect_getPhone(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '전화번호는 숫자로만 입력할 수 있어요\U0001F622\n대시(-)를 제외하고 입력해주시길 부탁드려요:)\n*전화번호를 입력해주세요.*'
  update.message.reply_text(message, parse_mode = 'Markdown')

  return JOIN_GET_PHONE

def getEmail(update, context):
  # Write Privacy info.
  if sql.modifyAccount(update.message.chat_id, ['phone'], [update.message.text]):
    # Logging Conversation
    convLog(update, convLogger)

    # Message
    message = '*이메일 주소를 입력해주세요.*\n예시: `teslaaurora@naver.com`'
    update.message.reply_text(message, parse_mode = 'Markdown')

    return JOIN_GET_EMAIL

  else: return getEmail(update, context)

def incorrect_getEmail(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '정확한 이메일 형식이 아니에요\U0001F627\n골뱅이와 도메인까지 입력해주셔야 해요:)\n*이메일 주소를 입력해주세요.*\nex. teslaaurora@naver.com'
  update.message.reply_text(message, parse_mode = 'Markdown')

  return JOIN_GET_EMAIL


#################### DEF: GET & VERIFY TOKEN ####################
def _keyboardMarkup_vehicles(update, context):
  # Vehicles Vars
  j, k = 0, 0
  keyboard = []
  keyboard.append([])

  # Markup Keyboard
  try:
    for i in sql.inquiryVehicle(update.message.chat_id, None, ['vehicle_name']):
      if len(keyboard[k]) == 2:
        keyboard.append([])
        k += 1
      keyboard[k].append(i[0])
      j += 1
    return keyboard

  except:
    keyboard = [['\U0001F519 돌아가기']]
    return keyboard

def getToken(update, context):
  # Write Privacy info.
  if sql.modifyAccount(update.message.chat_id, ['email'], [update.message.text]):
    # Logging Conversation
    convLog(update, convLogger)

    # Message
    message = '이제 한 가지 절차만 남았습니다!\U0001F60F\n본 서비스와 회원님의 차량이 연동되기 위해 Tesla 계정과 연결되는 토큰이 필요합니다.\n'\
            + '토큰은 종단 간 암호화되어 있으므로 개발자를 비롯한 중간의 *그 누구도 회원님의 계정 정보를 알 수 없습니다.*'
    update.message.reply_text(message, parse_mode = 'Markdown')

    message = '*토큰 발급 방법을 알려드릴게요!*\n'\
            + '\U00002714 우선, 토큰을 발급받을 수 있는 앱을 설치해야 합니다. '\
            + '바로가기: [iOS](https://apps.apple.com/kr/app/auth-app-for-tesla/id1552058613) 또는 '\
            + '[Android](https://play.google.com/store/apps/details?id=net.leveugle.teslatokens)\n'\
            + '\U00002714 앱에서 Tesla 계정으로 로그인하고, Refresh Token의 값을 복사하세요.\n'\
            + '\U00002714 복사한 값을 정확히 아래에 붙혀 넣으면 됩니다.'
    update.message.reply_text(message, parse_mode = 'Markdown', disable_web_page_preview = True)

    message = '*Refresh Token을 입력해주세요.*'
    update.message.reply_text(message, parse_mode = 'Markdown')

    return JOIN_GET_TOKEN

  else: return getToken(update, context)

def getToken_resume(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Message
  message = '본 서비스와 회원님의 차량이 연동되기 위해 Tesla 계정과 연결되는 토큰이 필요합니다.\n'\
          + '토큰은 종단 간 암호화되어 있으므로 개발자를 비롯한 중간의 *그 누구도 회원님의 계정 정보를 알 수 없습니다.*'
  update.message.reply_text(message, parse_mode = 'Markdown', reply_markup = ReplyKeyboardRemove())

  message = '*토큰 발급 방법을 알려드릴게요!*\n'\
          + '\U00002714 우선, 토큰을 발급받을 수 있는 앱을 설치해야 합니다. '\
          + '바로가기: [iOS](https://apps.apple.com/kr/app/auth-app-for-tesla/id1552058613) 또는 '\
          + '[Android](https://play.google.com/store/apps/details?id=net.leveugle.teslatokens)\n'\
          + '\U00002714 앱에서 Tesla 계정으로 로그인하고, Refresh Token의 값을 복사하세요.\n'\
          + '\U00002714 복사한 값을 정확히 아래에 붙혀 넣으면 됩니다.'
  update.message.reply_text(message, parse_mode = 'Markdown', disable_web_page_preview = True)

  message = '*Refresh Token을 입력해주세요.*'
  update.message.reply_text(message, parse_mode = 'Markdown')

  return JOIN_GET_TOKEN

def verifyToken(update, context):
  # Logging Conversation
  convLog(update, convLogger)

  # Delete the Token Information Message
  #update.message.delete()

  # Message
  message = '\U0001F4AB *토큰을 검증하고 있습니다...*\n'
  #message += '입력하신 메시지는 보안을 위해 저희가 삭제했습니다:)'
  editable_msg = update.message.reply_text(message, parse_mode = 'Markdown')

  # Verify Refresh Token & Get Access Token
  access_t = Token(update.message.chat_id).generate(update.message.text)

  # Succeeded Verify Token
  if access_t:
    if Token(update.message.chat_id).verify(access_t):
      # Message
      message = '\U0001F44F *토큰 검증을 성공했습니다!*\n'
      editable_msg.edit_text(message, parse_mode = 'Markdown')

      message = '\U0001F4AB *등록된 차량 목록을 가져오는 중입니다...*'
      editable_msg = update.message.reply_text(message, parse_mode = 'Markdown')
            
      '''
      if vehicle_cnts > 2:
        # Message
        message = '\U000026A0 *이런, 차량을 3대 이상 보유하고 계시군요.*\n'\
                + '3대 이상의 차량이 있는 Tesla 계정으로는 가입이 제한돼요:(\n'\
                + '서버 안정화를 위한 조치로, 더 많은 이용자가 쾌적하게 사용할 수 있게 하기 위함임을 양해해주셨으면 좋겠습니다\U0001F622\n'\
                + '새로운 Tesla 계정을 만들어 \'다른 운전자 추가\' 기능을 이용하신다면 서비스를 이용하실 수 있습니다.\n'\
                + '다음 기회에 다시 찾아뵙기를 희망합니다\U0001F3C3\n'\
                + '[테슬라 계정 생성 바로가기 링크](https://auth.tesla.com/oauth2/v1/register?redirect_uri=https%3A%2F%2Fwww.tesla.com%2Fteslaaccount%2Fowner-xp%2Fauth%2Fcallback&response_type=code&client_id=ownership&scope=offline_access+openid+ou_code+email&audience=https%3A%2F%2Fownership.tesla.com%2F&locale=ko-KR)'
                        
        editable_msg.edit_text(message, parse_mode = 'Markdown')
                
        return ConversationHandler.END
      '''

      vehicle_cnts = getVehCounts(update.message.chat_id, access_t)
      if sql.modifyAccount(update.message.chat_id, ['vehicle_counts'], [vehicle_cnts]):
        if generateVehicles(update.message.chat_id, access_t):
          message = '\U0001F44F *차량 목록을 가져왔습니다!*\n'
          editable_msg.edit_text(message, parse_mode = 'Markdown')

          # Write Privacy info.
          # Succeeded Write Token
          if sql.modifyAccount(update.message.chat_id, ['token_refresh', 'token_access'], [update.message.text, access_t]):
            if vehicle_cnts > 1:
              # Message
              message = '\U0001F607 *차량을 두 대 이상 보유하고 계시군요!*\n'\
                      + '보유한 차량 중에서 자주 사용하는 차량을 지정해야 합니다.\n'\
                      + '서비스 사용 시 차량 선택에 대한 절차를 간소화하기 위해 모든 기능은 설정된 자주 사용하는 차량에 대해 동작합니다.\n'\
                      + '자주 사용하는 차량은 한 대만 설정할 수 있으며, 계정 설정에서 언제든 변경할 수 있습니다:)\n'
              editable_msg.edit_text(message, parse_mode = 'Markdown')
              
              message = '*자주 사용하는 차량을 선택해주세요.*'
              keyboard = _keyboardMarkup_vehicles(update, context)
              
              reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
              update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

              return JOIN_DEFAULT_VEH
            
            elif vehicle_cnts == 0:
              # Message
              message = '\U0001F607 *아직 테슬라 차량이 없어요!*\n'\
                      + '테슬라 계정에 차량이 한 대 이상 등록되어 있어야 테슬라 오로라를 이용할 수 있습니다.\n'\
                      + '차량 출고 이전이라면 인도 수락 이후 다시 이용해주세요.'
              editable_msg.edit_text(message, parse_mode = 'Markdown')

              return ConversationHandler.END

            else:
              message = '\U0001F4AB *데이터를 저장하고 있습니다...*'
              editable_msg = update.message.reply_text(message, parse_mode = 'Markdown')

              for _ in getVehCurrent(update.message.chat_id): vID = _['id']
              if sql.modifyAccount(update.message.chat_id, ['default_vehicle'], [vID]):
                # Message
                message = '\U0001F44F *모든 데이터를 안전하게 저장했습니다!*\n'
                editable_msg.edit_text(message, parse_mode = 'Markdown')

                message = '테슬라 오로라의 가입이 완료되었습니다\U0001F973\n이제 오로라만의 다양한 기능을 누려보세요! \U0001F929\U0001F929'
                keyboard = [['\U0001F920']]

                reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
                update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

                return GOTO_MENU

              # Failed modifyAccount()
              else:
                # Message
                message = '\U000026A0 *데이터 저장에 실패했습니다.*\n@TeslaAurora 로 문의해주세요.'
                update.message.reply_text(message, parse_mode = 'Markdown')
                            
                return ConversationHandler.END

          # Failed Write Token
          else:
            # Message
            message = '\U000026A0 *데이터 저장에 실패했습니다.*\n@TeslaAurora 로 문의해주세요.'
            update.message.reply_text(message, parse_mode = 'Markdown')
                        
            return ConversationHandler.END

        # Failed createVehID
        else:
          # Message
          message = '\U000026A0 *차량 목록을 가져오는 데에 실패했습니다.*\n@TeslaAurora 로 문의해주세요.'
          editable_msg.edit_text(message, parse_mode = 'Markdown')
                    
          return ConversationHandler.END

      # Failed modifyAccount | countVeh
      else:
        # Message
        message = '\U000026A0 *차량 목록을 가져오는 데에 실패했습니다.*\n@TeslaAurora 로 문의해주세요.'
        editable_msg.edit_text(message, parse_mode = 'Markdown')
                
        return ConversationHandler.END
        
    # Failed Verify Token
    else:
      # Message
      message = '\U000026A0 *Token이 정확하지 않거나 유효하지 않습니다.*\n'
      editable_msg.edit_text(message, parse_mode = 'Markdown')

      message = '보내드린 메시지의 링크에 있는 앱에서 토큰을 발급하길 권장드리며, Access Token이 아닌 Refresh Token을 입력하셔야 합니다\U0001F62C\n'\
              + '지속적으로 오류가 발생한다면 @TeslaAurora 로 문의해주세요.'
      update.message.reply_text(message, parse_mode = 'Markdown')
                    
      message = '*Refresh Token을 입력해주세요.*'
      update.message.reply_text(message, parse_mode = 'Markdown')
    
  # Failed Verify Token
  else:
    # Message
    message = '\U000026A0 *Token이 정확하지 않거나 유효하지 않습니다.*\n'
    editable_msg.edit_text(message, parse_mode = 'Markdown')

    message = '보내드린 메시지의 링크에 있는 앱에서 토큰을 발급하길 권장드리며, Access Token이 아닌 Refresh Token을 입력하셔야 합니다\U0001F62C\n'\
            + '지속적으로 오류가 발생한다면 @TeslaAurora 로 문의해주세요.'
    update.message.reply_text(message, parse_mode = 'Markdown')
                
    message = '*Refresh Token을 입력해주세요.*'
    update.message.reply_text(message, parse_mode = 'Markdown')

def verifyVehicle(update, context):
  # Message
  message = '\U0001F4AB *차량을 확인하고 있습니다...*'
  editable_msg = update.message.reply_text(message, parse_mode = 'Markdown')
    
  # Verify Access Token
  if Token(update.message.chat_id).verify():
    # Vehicles Vars
    vID, vName = [], []

    # Logging Conversation
    convLog(update, convLogger)

    # Matching Vehicle(ID - DP_NAME)
    for i in getVehCurrent(update.message.chat_id):
      vID.insert(0, i['id'])
      vName.insert(0, i['display_name'])
      # [0]에 insert하면서 기존 데이터는 [1]로 옮겨짐
      
    # Verify Reply
    if update.message.text in vName:
      message = '\U0001F4AB *데이터를 저장하고 있습니다...*'
      editable_msg.edit_text(message, parse_mode = 'Markdown')

      _a = vID[vName.index(update.message.text)]
      if sql.modifyAccount(update.message.chat_id, ['default_vehicle'], [_a]):
        # Message
        message = '\U0001F44F *모든 데이터를 안전하게 저장했습니다!*\n'
        editable_msg.edit_text(message, parse_mode = 'Markdown')

        message = '테슬라 오로라의 가입이 완료되었습니다\U0001F973\n이제 오로라만의 다양한 기능을 누려보세요! \U0001F929\U0001F929'
        keyboard = [['\U0001F920']]

        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
        update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

        return GOTO_MENU

      # Failed modifyAccount()
      else:
        # Message
        message = '\U000026A0 *데이터 저장에 실패했습니다.*\n@TeslaAurora 로 문의해주세요.'
        editable_msg.edit_text(message, parse_mode = 'Markdown')
        
        return ConversationHandler.END

    else: # Not Matched Vehicle(ID - DP_NAME)
      # Message
      #context.bot.deleteMessage(message_id = editable_msg.message_id, chat_id = update.message.chat_id)
      message = '\U000026A0 *차량을 찾을 수 없습니다.*\n임의의 텍스트를 입력할 수 없어요:(\n'\
              + '아래 버튼에 표시되는 차량 이름이 올바르지 않다면 @TeslaAurora 로 문의해주세요.'
      editable_msg.edit_text(message, parse_mode = 'Markdown')

      message = '*차량을 선택해주세요.*'
      keyboard = _keyboardMarkup_vehicles(update, context)

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')

      return JOIN_DEFAULT_VEH
      
  else: # Token Expired
    # Message
    message = '\U000026A0 *액세스 토큰이 만료되었습니다.*\n토큰을 자동으로 갱신하고 있어요\U0001F609\n잠시만 기다려주세요.'
    editable_msg.edit_text(message, parse_mode = 'Markdown')

    # Renewal Access Token
    if Token(update.message.chat_id).renewal() == 0:
      context.bot.deleteMessage(
        message_id = editable_msg.message_id, chat_id = update.message.chat_id)
      return verifyVehicle(update, context)
    else:
      message = '\U000026A0 *토큰 갱신에 실패했습니다.*\n다시 한 번 시도해볼게요:(\n잠시만 기다려주세요.'
      editable_msg.edit_text(message, parse_mode = 'Markdown')

      # Renewal Access Token(1-More-Time)
      _a = Token(update.message.chat_id).renewal()
      if _a == 0:
        context.bot.deleteMessage(
          message_id = editable_msg.message_id, chat_id = update.message.chat_id)
        return verifyVehicle(update, context)

      else:
        if _a == 1: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: JOIN\_TOKEN\_GEN\_1\n'
        elif _a == 2: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: JOIN\_TOKEN\_GEN\_2\n'
        elif _a == 3: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: JOIN\_TOKEN\_GEN\_3\n'
        elif _a == 4: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: JOIN\_TOKEN\_GEN\_4\n'
        elif _a == 5: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: JOIN\_TOKEN\_GEN\_5\n'
        elif _a == 6: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: JOIN\_TOKEN\_GEN\_6\n'
        elif _a == 7: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: JOIN\_TOKEN\_GEN\_7\n'
        elif _a == 8: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: JOIN\_TOKEN\_GEN\_8\n'
        else: message = '\U000026A0 *토큰 갱신에 실패했습니다.*\nERRCODE: JOIN\_TOKEN\_GEN\_9\n'

      message += '@TeslaAurora 로 문의해주세요.'
      keyboard = [['\U0001F519 돌아가기']]

      context.bot.deleteMessage(
        message_id = editable_msg.message_id, chat_id = update.message.chat_id)

      # Logging Conversation
      convLog(update, convLogger)

      reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard = True, resize_keyboard = True)
      update.message.reply_text(message, reply_markup = reply_markup, parse_mode = 'Markdown')
            
      return GOTO_MENU
