package driftkings.views.utils
{
	import flash.filters.DropShadowFilter;
	import flash.text.*;
	import driftkings.views.utils.Constants;
	import driftkings.views.utils.Utils;
	
	public class TextExt extends TextField
	{
		public function TextExt(x:Number, y:Number, style:TextFormat, align:String, setShadow:Object, ui:*, enabled:Boolean = true)
		{
			super();
			if (style == null)
			{
				style = Constants.normalText;
			}
			this.x = x;
			this.y = y;
			this.width = 1;
			this.defaultTextFormat = style;
			this.antiAliasType = AntiAliasType.ADVANCED;
			this.autoSize = align;
			this.filters = [new DropShadowFilter(setShadow.distance = setShadow.distance, setShadow.angle, Utils.colorConvert(setShadow.color), setShadow.alpha, setShadow.blurX, setShadow.blurY, setShadow.strength, setShadow.quality, false, false, false)];
			this.selectable = false;
			this.multiline = true;
			this.visible = enabled;
			this.htmlText = "";
			ui.addChild(this);
		}
	}
}