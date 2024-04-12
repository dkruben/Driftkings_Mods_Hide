package driftkings.hangar
{
	import flash.display.Sprite;
	import flash.text.TextField;
	import flash.filters.DropShadowFilter;
	import flash.display.MovieClip;
	import flash.events.Event;
	import flash.events.MouseEvent;
	import scaleform.clik.events.ButtonEvent;

    import net.wg.gui.components.containers.MainViewContainer;
    import net.wg.infrastructure.base.AbstractView;
    import net.wg.infrastructure.events.LoaderEvent;
    import net.wg.infrastructure.interfaces.IManagedContent;
    import net.wg.infrastructure.interfaces.ISimpleManagedContainer;
    import net.wg.infrastructure.interfaces.IView;
    import net.wg.infrastructure.managers.impl.ContainerManagerBase;
	import net.wg.data.constants.generated.LAYER_NAMES;
    import net.wg.gui.lobby.hangar.Hangar;
	
    public class CreditCalculatorUI extends AbstractView
    {
		public var py_startPos:Function = null;
		public var py_newPos:Function = null;
		public var creditCalcContainer:Sprite = null;
		public var creditCalcText:TextField = null;
		public var creditCalcBackground:MovieClip = null;
		private var _dragging:Boolean = false;
		private var _draggingData:Array = null;
		private var _hangar:Hangar;	
		private var posX:int;
		private var posY:int;
		private var appWidht:Number = 1024;
		private var appHeight:Number = 768;
		
        override protected function onPopulate() : void
        {
           super.onPopulate();
        }
		
		public function as_setText(text:String) : void
		{
			var htmlData:String = text;
			try
			{
				this.creditCalcText.htmlText = htmlData;
				this.creditCalcBackground.width = this.creditCalcText.width;
				this.creditCalcBackground.height = this.creditCalcText.height;

				return;
			}
			catch(e:Error)
			{
				DebugUtils.LOG_ERROR("[ERROR] CreditCalculator: ",e.name);
				DebugUtils.LOG_ERROR(e.getStackTrace().toString());
				return;
			}
		}

		public function as_setPosition(x:Number, y:Number) : void
		{
			var _x:Number = x;
			var _y:Number = y;
			try
			{
				
				this.creditCalcBackground.x = _x;	
				this.creditCalcBackground.y = _y;
				
				return;
			}
			catch(e:Error)
			{
				DebugUtils.LOG_ERROR("[ERROR] CreditCalculator: ",e.name);
				DebugUtils.LOG_ERROR(e.getStackTrace().toString());
				return;
			}
		}	  

		public function as_setBackground(isEnabled:Boolean, bg_color:Number, bg_alpha:Number) : void
		{
			var bgenabled:Boolean = isEnabled;
			var bgcolor:Number = bg_color;
			var bgalpha:Number = bg_alpha;
			
			try
			{
				this.creditCalcBackground.visible = bgenabled;
				this.creditCalcBackground.graphics.clear();
				this.creditCalcBackground.graphics.beginFill(Number(bgcolor), Number(bgalpha));
				this.creditCalcBackground.graphics.drawRect(0, 0, 100, 100);
				this.creditCalcBackground.graphics.endFill();

				return;
			}
			catch(e:Error)
			{
				DebugUtils.LOG_ERROR("[ERROR] CreditCalculator: ",e.name);
				DebugUtils.LOG_ERROR(e.getStackTrace().toString());
				return;
			}
		}	 
	  
		override protected function configUI() : void
		{
			var num:int = 0;
			var idx:int = 0;
			var topmostView:IManagedContent = null;
			var view:IView = null;
			super.configUI();
			var viewContainer:MainViewContainer = this._getContainer(LAYER_NAMES.VIEWS) as MainViewContainer;
			if(viewContainer != null)
			{
				num = viewContainer.numChildren;
				for(idx = 0; idx < num; idx++)
				{
					view = viewContainer.getChildAt(idx) as IView;
					if(view != null)
					{
						this.processView(view);
					}
				}
				topmostView = viewContainer.getTopmostView();
				if(topmostView != null)
				{
					viewContainer.setFocusedView(topmostView);
				}
			}
			(App.containerMgr as ContainerManagerBase).loader.addEventListener(LoaderEvent.VIEW_LOADED,this.onViewLoaded,false,0,true);
		}

		private function onViewLoaded(event:LoaderEvent) : void
		{
			var view:IView = event.view as IView;
			this.processView(view);
		}
		
		private function _getContainer(containerName:String) : ISimpleManagedContainer
		{
			return App.containerMgr.getContainer(LAYER_NAMES.LAYER_ORDER.indexOf(containerName));
		}
 
        private function processView(view:IView) : void
        {
			
            if (view.as_config.alias == 'hangar')
            {  
				_hangar = view as Hangar;
                
				var filter:DropShadowFilter = null;
				
				
				this.creditCalcText = new TextField();
				this.creditCalcText.autoSize = "left";
				this.creditCalcText.htmlText = "";
				this.creditCalcText.multiline = true;
				this.creditCalcText.wordWrap = true;
				this.creditCalcText.width = 400;
				this.creditCalcText.height = 150;
				this.creditCalcText.selectable = false;
				filter = new DropShadowFilter();
				filter.distance = 0;
				filter.angle = 90;
				filter.color = Number(0);
				filter.alpha = 100;
				filter.blurX = filter.blurY = 5;
				filter.strength = 3;
				filter.quality = 3;
				filter.inner = false;
				filter.knockout = false;
				this.creditCalcText.filters = [filter];
				
				this.creditCalcBackground = new MovieClip();
                this.creditCalcBackground.visible = true;
                this.creditCalcBackground.width = this.creditCalcText.width;
                this.creditCalcBackground.height = this.creditCalcText.height;
                this.creditCalcBackground.graphics.clear();
                this.creditCalcBackground.graphics.beginFill(0x000000, 0.0);
                this.creditCalcBackground.graphics.moveTo(0,0);
                this.creditCalcBackground.graphics.lineTo(100,0);
                this.creditCalcBackground.graphics.lineTo(100,100);
                this.creditCalcBackground.graphics.lineTo(0,100);
                this.creditCalcBackground.graphics.lineTo(0,0);
                this.creditCalcBackground.graphics.endFill();
				this.creditCalcBackground.visible = false;
				
				this.creditCalcContainer = new Sprite();	
				this.creditCalcContainer.addChild(creditCalcBackground);
				this.creditCalcContainer.addChild(creditCalcText);
				this.creditCalcContainer.x = (App.appWidth + 400) / 2;	
				this.creditCalcContainer.y = 35;
				this.posX = int(this.creditCalcContainer.x - (App.appWidth / 2.0));
				this.posY = int(this.creditCalcContainer.y - (App.appHeight / 2.0));
				
				this.creditCalcContainer.addEventListener(MouseEvent.MOUSE_DOWN, handleMouseDown);
				this.creditCalcContainer.addEventListener(MouseEvent.MOUSE_UP, handleMouseUp);
				this.creditCalcContainer.addEventListener(MouseEvent.MOUSE_MOVE, handleMouseMove);

				view.addChild(this.creditCalcContainer);

            }
        }
		
		
		private function handleMouseDown(event:MouseEvent) : void 
		{
			_dragging = true;
			_draggingData = [int(this.creditCalcContainer.x), int(this.creditCalcContainer.y)];
			this.creditCalcContainer.startDrag();
		}
		
		private function handleMouseMove(event:MouseEvent) : void 
		{
			if (_dragging) 
			{
			}
		}
		
		private function handleMouseUp(event:MouseEvent) : void 
		{
			if (_dragging) 
			{
				_dragging = false;
				this.creditCalcContainer.stopDrag();
				
				this.posX = int(this.creditCalcContainer.x - (App.appWidth / 2.0));
				this.posY = int(this.creditCalcContainer.y - (App.appHeight / 2.0));
				this.py_newPos(this.creditCalcContainer.x, this.creditCalcContainer.y);
				
			}
		}
		
    }
}