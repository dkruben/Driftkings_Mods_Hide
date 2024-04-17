package components
{
	import flash.events.MouseEvent;
	import flash.text.TextField;
   
	public class AMButton extends TextField
	{
		private static const _mouseoutimg:String = "gui/flash/AccountsManager/AM_Icon_MouseOut.png";
		private static const _mouseoverimg:String = "gui/flash/AccountsManager/AM_Icon_MouseOver.png";
      
		private var _tooltip:String = "";
      
		public function AMButton()
		{
			super();
			htmlText = "<img width=\'39\' height=\'39\' src=\'img://" + _mouseoutimg + "\'>";
			width = 41;
			height = 41;
			selectable = false;
			addEventListener(MouseEvent.MOUSE_OVER,this.onMouseOver);
			addEventListener(MouseEvent.MOUSE_OUT,this.onMouseOut);
		}
      
		public function set tooltip(param1:String) : void
		{
			this._tooltip = param1;
		}
      
		public function onMouseOver(param1:MouseEvent) : void
		{
			htmlText = "<a href=\'event:#\'><img width=\'39\' height=\'39\' src=\'img://" + _mouseoverimg + "\'></a>";
			App.toolTipMgr.show(this._tooltip);
		}
      
		public function onMouseOut(param1:MouseEvent) : void
		{
			htmlText = "<img width=\'39\' height=\'39\' src=\'img://" + _mouseoutimg + "\'>";
			App.toolTipMgr.hide();
		}
	}
}