package driftkings.views.battle
{
   import driftkings.views.utils.Constants;
   import driftkings.views.utils.ProgressBar;
   import driftkings.views.utils.Align;
   import flash.events.Event;
   import flash.text.TextFieldAutoSize;
   import mods.common.BattleDisplayable;
   
   public class OwnHealthUI extends BattleDisplayable
   {
      private var own_health:ProgressBar;
      public var getAVGColor:Function;
      public var getSettings:Function;
	  
      private var alignX:String = Align.CENTER;
      private var alignY:String = Align.BOTTOM;
      
      public function OwnHealthUI()
      {
         super();
      }
      
      override protected function configUI() : void
      {
         super.configUI();
         this.tabEnabled = false;
         this.tabChildren = false;
         this.mouseEnabled = false;
         this.mouseChildren = false;
         this.buttonMode = false;
      }
      
      override protected function onPopulate() : void
      {
         super.onPopulate();
         this.onResizeHandle(null);
         var settings:Object = this.getSettings();
         var colors:Object = this.getSettings().colors;
         
         this.alignX = settings.alignX || Align.CENTER;
         this.alignY = settings.alignY || Align.BOTTOM;
         
         this.own_health = new ProgressBar(settings.x - 90, settings.y, 180, 22, this.getAVGColor(), colors.bgColor, 0.2);
         this.own_health.setOutline(180, 22);
         this.own_health.addTextField(90, -3, TextFieldAutoSize.CENTER, Constants.middleText);
         this.addChild(this.own_health);
         
         this.updatePosition();
      }
      
      private function updatePosition() : void
      {
         var posX:Number = App.appWidth >> 1;
         var posY:Number = App.appHeight >> 1;
         
         switch(this.alignX)
		 {
            case Align.LEFT:
               posX = 0;
               break;
            case Align.RIGHT:
               posX = App.appWidth;
               break;
         }
         
         switch(this.alignY)
		 {
            case Align.TOP:
               posY = 0;
               break;
            case Align.BOTTOM:
               posY = App.appHeight;
               break;
         }
         
         this.x = posX;
         this.y = posY;
      }
      
      override protected function onBeforeDispose() : void
      {
         super.onBeforeDispose();
         this.own_health.remove();
         this.own_health = null;
      }
      
      public function as_setOwnHealth(scale:Number, text:String, color:String) : void
      {
         this.own_health.setNewScale(scale);
         this.own_health.setText(text);
         this.own_health.updateColor(color);
      }
      
      public function as_BarVisible(isVisible:Boolean) : void
      {
         this.own_health.visible = isVisible;
      }
      
      private function onResizeHandle(event:Event) : void
      {
         this.updatePosition();
      }
      
      public function as_onCrosshairPositionChanged(x:Number, y:Number) : void
      {
         this.x = x;
         this.y = y;
      }
   }
}