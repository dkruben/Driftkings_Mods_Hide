package driftkings.views
{
	// FLASH IMPORTS
	import flash.display.DisplayObject;
	import flash.display.MovieClip;
	import flash.events.Event;
	import flash.events.MouseEvent;
	import flash.filters.DropShadowFilter;
	import flash.text.TextField;
	import flash.text.TextFieldAutoSize;
	import flash.utils.clearTimeout;
	import flash.utils.setTimeout;
	// WG IMPORTS
	import net.wg.infrastructure.base.UIComponentEx;
   
	public class InfoPanel extends UIComponentEx
	{
		public var posX:Number;
		public var posY:Number;

		private var isVisibleBB:Boolean = false;
		private var textField:TextField = null;
		private var bbox:MovieClip = null;
		private var textWidth:Number = 0;
		private var textHeight:Number = 0;
      
		public function InfoPanel()
		{
			super();
			this.textField = new TextField();
			this.textField.selectable = false;
			this.textField.autoSize = TextFieldAutoSize.LEFT;
			this.textField.multiline = true;
			this.textField.htmlText = "";
			addChild(this.createBB());
			addChild(this.textField);
		}
      
		override protected function configUI() : void
		{
			super.configUI();
			this.textField.addEventListener(MouseEvent.MOUSE_OVER,this.onMouseEevnt);
			this.textField.addEventListener(MouseEvent.MOUSE_OUT,this.onMouseEevnt);
			this.textField.addEventListener(MouseEvent.MOUSE_DOWN,this.onMouseEevnt);
			this.textField.addEventListener(MouseEvent.MOUSE_UP,this.onMouseEevnt);
			this.textField.addEventListener(MouseEvent.MOUSE_MOVE,this.onMouseEevnt);
			App.instance.stage.addEventListener(Event.RESIZE,this.onResize);
		}
      
		override protected function onDispose() : void
		{
			App.instance.stage.removeEventListener(Event.RESIZE,this.onResize);
			this.textField.removeEventListener(MouseEvent.MOUSE_OVER,this.onMouseEevnt);
			this.textField.removeEventListener(MouseEvent.MOUSE_OUT,this.onMouseEevnt);
			this.textField.removeEventListener(MouseEvent.MOUSE_DOWN,this.onMouseEevnt);
			this.textField.removeEventListener(MouseEvent.MOUSE_UP,this.onMouseEevnt);
			this.textField.removeEventListener(MouseEvent.MOUSE_MOVE,this.onMouseEevnt);
			removeChild(this.textField);
			this.textField = null;
			removeChild(this.bbox);
			this.bbox = null;
			super.onDispose();
		}
      
		private function onResize(e:Event) : void
		{
			this.setPosition(x,y);
		}
      
		private function onMouseEevnt(event:MouseEvent) : void
		{
			switch(event.type)
			{
				case MouseEvent.MOUSE_OVER:
					App.cursor.as_setCursor("dragopen");
					break;
				case MouseEvent.MOUSE_OUT:
					App.cursor.as_setCursor("arrow");
					this.stopDrag();
					break;
				case MouseEvent.MOUSE_DOWN:
					App.cursor.as_setCursor("dragclose");
					startDrag();
					break;
				case MouseEvent.MOUSE_UP:
					App.cursor.as_setCursor("dragopen");
					this.stopDrag();
			}
		}
      
		override public function stopDrag() : void
		{
			super.stopDrag();
			var new_x:Number = this.textField.x + x;
			var new_y:Number = this.textField.y + y;
			x = 0;
			y = 0;
			this.setPosition(new_x, new_y, false);
			this.onUpdatePosition(this.textField.x, this.textField.y);
		}
      
		public function setScale(w:Number, h:Number) : void
		{
			this.textWidth = w;
			this.textHeight = h;
			this.textField.wordWrap = w > 0;
			this.textField.wordWrap = h > 0;
			this.textField.width = Math.max(w,this.textField.width);
			this.textField.height = Math.max(h, this.textField.height);
			this._update();
		}
      
		public function setText(labelText:String) : void
		{
			this.textField.htmlText = labelText;
			this.setScale(this.textWidth, this.textHeight);
		}
		
		public function isDraggable(isDrag:Boolean): void
		{
			this.textField.mouseEnabled = isDrag;
		}
		
		public function setVisible(isVisible:Boolean): void
		{
			visible = isVisible;
		}
		
		public function hide(delay:int = 0):void
		{
			if (delay == 0)
			{
				this.textField.visible = false;
			}
			else
			{
				this.textField.visible = true;
			}
		}
      
		public function setVisibleBB(isVisible:Boolean) : void
		{
			this.isVisibleBB = isVisible;
			this._update();
		}
      
		public function setPosition(posX:Number, posY:Number, isSave:Boolean = true): void
		{
			var validated:Array = this.checkScreen(this.textField as DisplayObject, posX, posY);
			if(validated[2])
			{
				posX = validated[0];
				posY = validated[1];
				if(isSave)
				{
					this.onUpdatePosition(posX, posY);
				}
			}
			this.textField.x = posX;
			this.textField.y = posY;
			this._update();
			var _x:Number = posX;
			var _y:Number = posY;
		}
      
		public function setShadow(linkage:Object) : void
		{
			var filter:DropShadowFilter = new DropShadowFilter();
			filter.distance = linkage.distance;
			filter.angle = linkage.angle;
			filter.color = parseInt("0x" + linkage.color.split("#").join(""), 16);
			filter.alpha = linkage.alpha;
			filter.blurX = linkage.blurX;
			filter.blurY = linkage.blurY;
			filter.strength = linkage.strength;
			filter.quality = linkage.quality;
			filter.hideObject = false;
			filter.inner = false;
			filter.knockout = false;
			this.textField.filters = [filter];
		}
      
		private function _update() : void
		{
			this.bbox.visible = this.isVisibleBB;
			var x:Number = 5;
			var y:Number = 5;
			this.bbox.graphics.clear();
			this.bbox.graphics.lineStyle(1, 0x999999, 1, true);
			this.bbox.graphics.beginFill(0x999999, 0.1);
			this.bbox.graphics.drawRect(-x, -y, this.textField.width + 2 * x, this.textField.height + 2 * y);
			this.bbox.graphics.endFill();
			this.bbox.x = this.textField.x;
			this.bbox.y = this.textField.y;
		}
      
		private function createBB() : MovieClip
		{
			this.bbox = new MovieClip();
			this.bbox.visible = false;
			this._update();
			return this.bbox;
		}
      
		private function checkScreen(target:DisplayObject, posX:Number, posY:Number) : Array
		{
			var isChanged:Boolean = false;
			if(posX + target.width > App.appWidth)
			{
				posX = App.appWidth - target.width;
				isChanged = true;
			}
			else if(posX < 0)
			{
				posX = 0;
				isChanged = true;
			}
			if(posY + target.height > App.appHeight)
			{
				posY = App.appHeight - target.height;
				isChanged = true;
			}
			else if(posY < 0)
			{
				posY = 0;
				isChanged = true;
			}
			return [posX,posY,isChanged];
		}
      
		private function onUpdatePosition(newX:Number, newY:Number) : void
		{
			this.posX = newX;
			this.posY = newY;
			dispatchEvent(new Event(Event.CHANGE));
		}
	}
}