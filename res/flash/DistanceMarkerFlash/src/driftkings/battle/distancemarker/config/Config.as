package driftkings.battle.distancemarker.config 
{
	import driftkings.battle.distancemarker.utils.Disposable;

	public class Config implements Disposable
	{
		private var _decimalPrecision:int= 0;
		private var _textSize:int = 11;
		private var _textColor:int = 0xFFFFFF;
		private var _textAlpha:Number = 1.0;
		private var _drawTextShadow:Boolean = true;
		
		public function Config() 
		{
			super()
		}
		
		public function deserialize(serializedConfig:Object) : void
		{
            this._decimalPrecision = serializedConfig["decimalPrecision"];
            this._textSize = serializedConfig["textSize"];
            this._textColor = uint(serializedConfig["textColor"]); // Convert string to uint
            this._textAlpha = serializedConfig["textAlpha"];
            this._drawTextShadow = serializedConfig["drawTextShadow"];
        }
		
		public function disposeState() : void
		{}
		
		public function get decimalPrecision() : int
		{
			return this._decimalPrecision;
		}
		
		public function get textSize() : int
		{
			return this._textSize;
		}
		
		public function get textColor() : int
		{
			return this._textColor;
		}
		
		public function get textAlpha() : Number
		{
			return this._textAlpha;
		}
		
		public function get drawTextShadow() : Boolean
		{
			return this._drawTextShadow;
		}
	}
}