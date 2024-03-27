package driftkings.views.battle
{
	import flash.display.*;
	import flash.events.Event;
	import flash.events.IOErrorEvent;
	import flash.net.URLRequest;
	import flash.text.TextFieldAutoSize;
	//
	import driftkings.views.utils.Constants;
	import driftkings.views.utils.TextExt;
	import driftkings.views.utils.tween.Tween;
	//
	import mods.common.BattleDisplayable;
	
	public class SixthSenseUI extends BattleDisplayable
	{
		private var loader:Loader;
		private var params:Object;
		private var timer:TextExt;
		private var _container:Sprite;
		private var hideAnimation:Tween;
		private var showAnimation:Tween;
		private var hideAnimation2:Tween;
		private var posY:Number = (App.appHeight >> 3) + 10;
		public var getSettings:Function;
		
		[Embed(source = "error.png")]
		private var DefaultIcon:Class;

		public function SixthSenseUI()
		{
			super();
			this.loader = new Loader();
			this.loader.contentLoaderInfo.addEventListener(Event.COMPLETE, this.imageLoaded);
			this.loader.contentLoaderInfo.addEventListener(IOErrorEvent.IO_ERROR, this.onLoadError);;
		}
		
		override protected function configUI():void
		{
			super.configUI();
			this.tabEnabled = false;
			this.tabChildren = false;
			this.mouseEnabled = false;
			this.mouseChildren = false;
			this.buttonMode = false;
		}
		
		override protected function onPopulate():void
		{
			super.onPopulate();
			this.params = this.getSettings();
			this.x = App.appWidth >> 1;
			this._container = new Sprite()
			this.addChild(_container);
			if (this.params.defaultIcon)
			{
				this.loader.load(new URLRequest('../../gui/maps/icons/SixthSense/' + this.params.defaultIconName + '.png'
				));
			}
			else
			{
				this.loader.load(new URLRequest('../../../' + this.params.userIcon));
			}
		}
		
		override protected function onBeforeDispose():void
		{
			super.onBeforeDispose();
			this.loader.contentLoaderInfo.removeEventListener(Event.COMPLETE, this.imageLoaded);
			this.loader.contentLoaderInfo.removeEventListener(IOErrorEvent.IO_ERROR, this.onLoadError);
			this.loader = null;
			this.hideAnimation.stop();
			this.hideAnimation2.stop();
			this.showAnimation.stop();
			this.hideAnimation = null;
			this.hideAnimation2 = null;
			this.showAnimation = null;
			this._container.removeChildren();
			this.timer = null;
			this._container = null;
			App.utils.data.cleanupDynamicObject(this.params);
		}

		private function addLoadedImageAndTimer(image:Bitmap):void
		{
			image.width = 150;
			image.height = 150;
			image.smoothing = true;
			this._container.addChild(image);
			this.timer = new TextExt(image.width >> 1, image.height - 8, Constants.tite16, TextFieldAutoSize.CENTER, this._container);
			this.hideAnimation = new Tween(this._container, "y", this.posY, -image.height, 0.5);
			this.hideAnimation2 = new Tween(this._container, "alpha", 1.0, 0, 0.5);
			this.showAnimation = new Tween(this._container, "alpha", 0, 1.0, 0.1);
			this._container.alpha = 0;
			this._container.x = -image.width >> 1;
			this._container.y = this.posY;
		}
		
		public function as_show():void
		{
			if (this.hideAnimation.isPlaying)
			{
				this.hideAnimation.stop();
				this.hideAnimation.rewind();
				this.hideAnimation2.stop();
				this.hideAnimation2.rewind();
			}
			this._container.y = this.posY;
			this.showAnimation.start();
		}
		
		public function as_hide():void
		{
			this.hideAnimation.start();
			this.hideAnimation2.start();
		}
		
		public function as_updateTimer(text:String):void
		{
			this.timer.htmlText = text;
		}
		
		private function onLoadError(e:IOErrorEvent):void
		{
			this.loader.close();
			this.addLoadedImageAndTimer(new DefaultIcon() as Bitmap);
		}
		
		private function imageLoaded(e:Event):void
		{
			this.addLoadedImageAndTimer(this.loader.content as Bitmap);
			this.loader.unload();
		}
		
		private function onResizeHandle(event:Event):void
		{
			this.x = App.appWidth >> 1;
			this.posY = (App.appHeight >> 3) + 10;
		}
	}
}